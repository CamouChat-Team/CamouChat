"""WhatsApp message processor with storage and filtering support."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import weakref
from logging import Logger, LoggerAdapter
from typing import List, Optional, Sequence, Union, Literal, cast

from playwright.async_api import Page

from camouchat.Decorators.Chat_Click_decorator import ensure_chat_clicked
from camouchat.Exceptions.whatsapp import (
    MessageNotFoundError,
    WhatsAppError,
    MessageProcessorError,
    MessageListEmptyError,
)
from camouchat.Filter.message_filter import MessageFilter
from camouchat.Interfaces.message_processor_interface import MessageProcessorInterface
from camouchat.Interfaces.storage_interface import StorageInterface
from camouchat.NoOpPattern import NoOpStorage, NoOpMessageFilter
from camouchat.WhatsApp.chat_processor import ChatProcessor
from camouchat.WhatsApp.models.chat import Chat
from camouchat.WhatsApp.models.message import Message
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig


class MessageProcessor(MessageProcessorInterface[Message, WebSelectorConfig]):
    """Extracts, encrypts (optionally), and stores messages from WhatsApp Web UI.

    Encryption behavior
    --------------------
    When an ``encryption_key`` is supplied:

    - Message body (``raw_data``) is encrypted with AES-256-GCM and the
      plaintext is blanked, so ciphertext and plaintext never coexist in
      the same database row.
    - Chat name (``parent_chat_name``) is encrypted with AES-256-GCM; the
      database index column stores a stable HMAC-SHA256 digest instead of
      the real name, keeping queries functional without exposing it.
    - The raw key is deleted from memory immediately after the encryptor is
      initialized.
    """

    _instances: weakref.WeakKeyDictionary[Page, MessageProcessor] = weakref.WeakKeyDictionary()
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> MessageProcessor:
        page = kwargs.get("page") or (args[4] if len(args) > 4 else None)
        if page is None:
            return super(MessageProcessor, cls).__new__(cls)

        if page not in cls._instances:
            instance = super(MessageProcessor, cls).__new__(cls)
            cls._instances[page] = instance
        return cls._instances[page]

    def __init__(
        self,
        chat_processor: ChatProcessor,
        page: Page,
        ui_config: WebSelectorConfig,
        storage_obj: Optional[StorageInterface] = None,
        filter_obj: Optional[MessageFilter] = None,
        encryption_key: Optional[bytes] = None,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__(
            storage_obj=storage_obj,
            filter_obj=filter_obj,
            log=log,
            page=page,
            UIConfig=ui_config,
        )

        self.storage = storage_obj or NoOpStorage()
        self.filter = filter_obj or NoOpMessageFilter()

        if storage_obj is None:
            self.log.info("Storage not provided → using NoOpStorage.")

        if filter_obj is None:
            self.log.info("Filter not provided → using NoOpMessageFilter.")

        self.chat_processor = chat_processor

        self.encryptor = None
        self._hmac_key: Optional[bytes] = None

        if encryption_key:
            try:
                from camouchat.Encryption import MessageEncryptor

                self.encryptor = MessageEncryptor(encryption_key)
                self._hmac_key = hashlib.sha256(encryption_key + b"chat-name-index").digest()[:16]
                self.log.info("Message encryption enabled (body + chat name).")
            except Exception as e:
                self.log.error(f"Failed to initialise encryptor: {e}")
                self.encryptor = None
                self._hmac_key = None
            finally:
                del encryption_key

        if self.page is None:
            raise ValueError("page must not be None")
        self._initialized = True

    def _hmac_chat_name(self, chat_name: str) -> str:
        """Return a stable HMAC-SHA256 hex digest of the chat name.

        Used as the queryable ``parent_chat_name`` index value when encryption
        is enabled — the real name is stored encrypted in ``encrypted_chat_name``.
        """
        assert self._hmac_key is not None
        return hmac.new(  # type: ignore[attr-defined]
            self._hmac_key, chat_name.encode(), hashlib.sha256
        ).hexdigest()

    def _encrypt_chat_name(self, chat_name: str) -> tuple[str, str, str]:
        """Encrypt chat name.

        Returns:
            Tuple of (hmac_digest, b64_ciphertext, b64_nonce).
        """
        assert self.encryptor is not None
        nonce, ciphertext = self.encryptor.encrypt(chat_name)
        return (
            self._hmac_chat_name(chat_name),
            base64.b64encode(ciphertext).decode(),
            base64.b64encode(nonce).decode(),
        )

    @staticmethod
    async def sort_messages(msgList: Sequence[Message], incoming: bool) -> List[Message]:
        """Filter messages by direction (incoming or outgoing)."""
        if not msgList:
            raise MessageListEmptyError("Empty list passed in sort messages.")

        if incoming:
            return [msg for msg in msgList if msg.direction == "in"]
        return [msg for msg in msgList if msg.direction == "out"]

    @ensure_chat_clicked(lambda self, chat: self.chat_processor._click_chat(chat))
    async def _get_wrapped_Messages(self, chat: Chat, retry: int, **kwargs) -> List[Message]:

        sc = self.UIConfig

        for attempt in range(1, retry + 1):
            try:
                wrapped_list: List[Message] = []

                all_Msgs = await sc.messages()
                count = await all_Msgs.count()

                if count == 0:
                    raise MessageNotFoundError("No messages found.")

                for i in range(count):
                    msg = all_Msgs.nth(i)

                    text = await sc.get_message_text(msg)
                    data_id = await sc.get_dataID(msg)

                    for _ in range(3):
                        if data_id:
                            break
                        data_id = await sc.get_dataID(msg)

                    if not data_id:
                        self.log.debug("Skipping message (missing data_id).")
                        continue

                    wrapped_list.append(
                        Message(
                            message_ui=msg,
                            direction=cast(
                                Literal["in", "out"],
                                "in" if await msg.locator(".message-in").count() > 0 else "out",
                            ),
                            raw_data=text,
                            parent_chat=chat,
                            data_id=data_id,
                        )
                    )

                return wrapped_list

            except WhatsAppError as e:
                if attempt < retry:
                    self.log.debug(f"[Retry {attempt}/{retry}] WhatsAppError: {e}")
                    await asyncio.sleep(0.5)
                else:
                    self.log.error(f"Failed after {retry} retries (WhatsAppError).")
                    raise MessageProcessorError(
                        f"Failed to wrap messages after {retry} retries."
                    ) from e

            except Exception as e:
                self.log.error("Unexpected error during message extraction", exc_info=True)
                raise MessageProcessorError("Unexpected failure.") from e
        raise MessageProcessorError("Unreachable state reached in message extraction.")

    async def fetch_messages(  # type: ignore[override]
        self, chat: Chat, retry: Optional[int] = 5, **kwargs
    ) -> List[Message]:
        """Fetch, optionally encrypt, store, and filter messages from a chat.
        param :
            chat (Chat): Chat to fetch messages from.
            retry (int): Number of times to retry the request. Default set to 5
        kwargs :
            only_new (bool): If True, returns only new messages.
        """

        msgList = await self._get_wrapped_Messages(chat, retry, **kwargs)

        # -----------------------------
        # Storage + Dedup
        # -----------------------------
        new_msgs = [
            msg
            for msg in msgList
            if not await self.storage.check_message_if_exists_async(msg_id=msg.message_id)
        ]

        # -----------------------------
        # Encryption Layer
        # -----------------------------
        if self.encryptor and new_msgs:
            chat_name = chat.chat_name
            chat_hmac, enc_chat_b64, chat_nonce_b64 = self._encrypt_chat_name(chat_name)

            for msg in new_msgs:
                raw = msg.raw_data or ""

                if raw:
                    try:
                        nonce, ciphertext = self.encryptor.encrypt_message(raw, msg.message_id)
                        msg.encrypted_message = base64.b64encode(ciphertext).decode()
                        msg.encryption_nonce = base64.b64encode(nonce).decode()
                        msg.raw_data = ""
                    except Exception as e:
                        self.log.warning(f"Failed to encrypt message {msg.message_id}: {e}")
                else:
                    self.log.debug(f"Skipping encryption (non-text): {msg.message_id}")

                msg.encrypted_chat_name = enc_chat_b64
                msg.chat_name_nonce = chat_nonce_b64
                msg.parent_chat_name_index = chat_hmac

        # -----------------------------
        # Storage (NoOp safe)
        # -----------------------------
        if new_msgs:
            await self.storage.enqueue_insert(msgs=new_msgs)
            self.log.debug(f"Stored {len(new_msgs)}/{len(msgList)} messages.")

        # -----------------------------
        # Filtering (NoOp safe)
        # -----------------------------
        if new_msgs:
            allowed_new = self.filter.apply(msgs=new_msgs)
            # Reconstruct list: old messages + allowed new messages
            # (Applying filter to all msgs repeatedly flags old messages as spam)
            msgList = [m for m in msgList if m not in new_msgs] + allowed_new
        else:
            allowed_new = []

        if kwargs.get("only_new", False):
            return allowed_new

        return msgList
