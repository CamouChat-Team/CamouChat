"""WhatsApp message processor with storage and filtering support."""

from __future__ import annotations

import asyncio
import base64
import weakref
from logging import Logger, LoggerAdapter
from typing import List, Optional, Sequence, Union

from playwright.async_api import Page

from camouchat.WhatsApp.decorator import ensure_chat_clicked
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
        if encryption_key:
            try:
                from camouchat.Encryption import MessageEncryptor

                self.encryptor = MessageEncryptor(encryption_key)
                self.log.info("Message encryption enabled (body).")
            except Exception as e:
                self.log.error(f"Failed to initialise encryptor: {e}")
                self.encryptor = None
            finally:
                del encryption_key

        if self.page is None:
            raise ValueError("page must not be None")
        self._initialized = True

    @staticmethod
    async def sort_messages(msgList: Sequence[Message], incoming: bool) -> List[Message]:
        """Filter messages by direction (incoming or outgoing)."""
        if not msgList:
            raise MessageListEmptyError("Empty list passed in sort messages.")

        if incoming:
            return [msg for msg in msgList if not msg.fromMe]
        return [msg for msg in msgList if msg.fromMe]

    @ensure_chat_clicked(lambda self, chat: self.chat_processor._click_chat(chat))
    async def _get_wrapped_Messages(self, chat: Chat, retry: int) -> List[Message]:

        assert self.UIConfig is not None
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
                    data_id: str = await sc.get_dataID(msg)

                    for _ in range(3):
                        if data_id:
                            break
                        data_id = await sc.get_dataID(msg)

                    if not data_id:
                        self.log.debug("Skipping message (missing data_id).")
                        continue

                    wrapped_list.append(
                        Message(
                            ui=msg,
                            fromMe=await msg.locator(".message-out").count() > 0,
                            body=text,
                            from_chat=chat,
                            id_serialized=data_id,
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

        msgList = await self._get_wrapped_Messages(chat, retry)

        # -----------------------------
        # Storage + Dedup
        # -----------------------------
        new_msgs = [
            msg
            for msg in msgList
            if not await self.storage.check_message_if_exists_async(msg_id=msg.id_serialized)
        ]

        # -----------------------------
        # Encryption Layer
        # -----------------------------
        if self.encryptor and new_msgs:
            for msg in new_msgs:
                raw = msg.body or ""

                if raw:
                    try:
                        nonce, ciphertext = self.encryptor.encrypt_message(raw, msg.id_serialized)
                        msg.body = base64.b64encode(ciphertext).decode()
                        msg.encryption_nonce = base64.b64encode(nonce).decode()
                    except Exception as e:
                        self.log.warning(f"Failed to encrypt message {msg.id_serialized}: {e}")
                else:
                    self.log.debug(f"Skipping encryption (non-text): {msg.id_serialized}")

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
