"""WhatsApp message processor with storage and filtering support."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from typing import List, Optional, Sequence

from playwright.async_api import Page

from src.Decorators.Chat_Click_decorator import ensure_chat_clicked
from src.Exceptions.whatsapp import (
    MessageNotFoundError,
    WhatsAppError,
    MessageProcessorError,
    MessageListEmptyError,
)
from src.FIlter.message_filter import MessageFilter
from src.Interfaces.message_processor_interface import MessageProcessorInterface
from src.Interfaces.storage_interface import StorageInterface
from src.WhatsApp.DerivedTypes.Chat import whatsapp_chat
from src.WhatsApp.DerivedTypes.Message import whatsapp_message
from src.WhatsApp.chat_processor import ChatProcessor
from src.WhatsApp.web_ui_config import WebSelectorConfig


class MessageProcessor(MessageProcessorInterface):
    """Extracts, encrypts (optionally), and stores messages from WhatsApp Web UI.

    Encryption behaviour
    --------------------
    When an ``encryption_key`` is supplied:

    - Message body (``raw_data``) is encrypted with AES-256-GCM and the
      plaintext is blanked, so ciphertext and plaintext never coexist in
      the same database row.
    - Chat name (``parent_chat_name``) is encrypted with AES-256-GCM; the
      database index column stores a stable HMAC-SHA256 digest instead of
      the real name, keeping queries functional without exposing it.
    - The raw key is deleted from memory immediately after the encryptor is
      initialised.
    """

    def __init__(
        self,
        storage_obj: Optional[StorageInterface],
        filter_obj: Optional[MessageFilter],
        chat_processor: ChatProcessor,
        page: Page,
        log: logging.Logger,
        UIConfig: WebSelectorConfig,
        encryption_key: Optional[bytes] = None,
    ) -> None:
        super().__init__(
            storage_obj=storage_obj,
            filter_obj=filter_obj,
            log=log,
            page=page,
            UIConfig=UIConfig,
        )
        self.chat_processor = chat_processor

        self.encryptor = None
        self._hmac_key: Optional[bytes] = None

        if encryption_key:
            try:
                from src.Encryption import MessageEncryptor

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

    def _hmac_chat_name(self, chat_name: str) -> str:
        """Return a stable HMAC-SHA256 hex digest of the chat name.

        Used as the queryable ``parent_chat_name`` index value when encryption
        is enabled — the real name is stored encrypted in ``encrypted_chat_name``.
        """
        assert self._hmac_key is not None
        return hmac.new(  # type: ignore[attr-defined]
            self._hmac_key, chat_name.encode("utf-8"), hashlib.sha256
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
            base64.b64encode(ciphertext).decode("utf-8"),
            base64.b64encode(nonce).decode("utf-8"),
        )

    @staticmethod
    async def sort_messages(
        msgList: Sequence[whatsapp_message], incoming: bool
    ) -> List[whatsapp_message]:
        """Filter messages by direction (incoming or outgoing)."""
        if not msgList:
            raise MessageListEmptyError("Empty list passed in sort messages.")

        if incoming:
            return [msg for msg in msgList if msg.direction == "in"]
        return [msg for msg in msgList if msg.direction == "out"]

    @ensure_chat_clicked(lambda self, chat: self.chat_processor._click_chat(chat))
    async def _get_wrapped_Messages(
        self, chat: whatsapp_chat, retry: int = 3, *args, **kwargs
    ) -> List[whatsapp_message]:

        wrapped_list: List[whatsapp_message] = []
        try:
            sc = self.UIConfig
            all_Msgs = await sc.messages()
            count = await all_Msgs.count()
            c = 0
            while c < retry and count == 0:
                all_Msgs = await sc.messages()
                count = await all_Msgs.count()
                c += 1

            if not count:
                raise MessageNotFoundError("Messages Not able to extract")

            for i in range(count):
                msg = all_Msgs.nth(i)
                text = await sc.get_message_text(msg)
                data_id = await sc.get_dataID(msg)

                c2 = 0
                while not data_id and c2 < 3:
                    data_id = await sc.get_dataID(msg)
                    c2 += 1

                if not data_id:
                    self.log.debug("Data ID is None/Empty — skipping message.")
                    continue

                wrapped_list.append(
                    whatsapp_message(
                        message_ui=msg,
                        direction="in" if await msg.locator(".message-in").count() > 0 else "out",
                        raw_data=text,
                        parent_chat=chat,
                        data_id=data_id,
                    )
                )

            return wrapped_list
        except WhatsAppError as e:
            raise MessageProcessorError("failed to wrap messages") from e

    async def Fetcher(  # type: ignore[override]
        self, chat: whatsapp_chat, retry: int, *args, **kwargs
    ) -> List[whatsapp_message]:
        """Fetch, optionally encrypt, store, and filter messages from a chat."""
        msgList = await self._get_wrapped_Messages(chat, retry, *args, **kwargs)

        if self.storage and msgList:
            new_msgs = [
                msg
                for msg in msgList
                if not await self.storage.check_message_if_exists_async(msg.message_id)
            ]
            if new_msgs:
                if self.encryptor:
                    chat_name = chat.chat_name
                    chat_hmac, enc_chat_b64, chat_nonce_b64 = self._encrypt_chat_name(chat_name)

                    for msg in new_msgs:
                        raw = msg.raw_data or ""
                        if raw:
                            try:
                                nonce, ciphertext = self.encryptor.encrypt_message(
                                    raw, msg.message_id
                                )
                                msg.encrypted_message = base64.b64encode(ciphertext).decode("utf-8")
                                msg.encryption_nonce = base64.b64encode(nonce).decode("utf-8")
                                msg.raw_data = ""
                            except Exception as e:
                                self.log.warning(f"Failed to encrypt message {msg.message_id}: {e}")
                        else:
                            self.log.debug(
                                f"Skipping body encryption for non-text message {msg.message_id}"
                            )

                        msg.encrypted_chat_name = enc_chat_b64
                        msg.chat_name_nonce = chat_nonce_b64
                        msg.parent_chat_name_index = chat_hmac

                await self.storage.enqueue_insert(new_msgs)
                self.log.debug(f"Enqueued {len(new_msgs)}/{len(msgList)} new messages for storage.")

        if self.filter:
            msgList = self.filter.apply(msgList)

        return msgList
