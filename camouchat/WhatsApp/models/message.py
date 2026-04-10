"""WhatsApp Message Class contracted with Message Interface Template"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Union, Optional

from playwright.async_api import ElementHandle, Locator

from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.WhatsApp.models.chat import Chat


@dataclass
class Message(MessageInterface):
    """Represents a WhatsApp message entity with safe logging and structured metadata."""

    fromMe: bool

    body: str
    from_chat: Chat
    ui: Optional[Union[ElementHandle, Locator]]
    msgtype: Optional[str] = None
    id_serialized: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    # Encryption fields
    encryption_nonce: Optional[str] = None

    def __post_init__(self):
        self.message_id = self._message_key()

    def _message_key(self) -> str:
        return f"wa-msg::{self.id_serialized}"

    # -----------------------------

    def isIncoming(self) -> Optional[bool]:
        """Returns True if incoming, False if outgoing."""
        return not self.fromMe

    def is_encrypted(self) -> bool:
        """Check if message content is encrypted."""
        return self.encryption_nonce is not None

    # -----------------------------

    def __str__(self) -> str:
        """User-friendly print (safe for logs, no sensitive leakage)."""

        direction = "OUT" if self.fromMe else "IN"

        # Safe preview (avoid dumping full message)
        preview = (self.body or "").replace("\n", " ").strip()
        preview = preview[:50] + ("..." if len(preview) > 50 else "")

        chat_name = getattr(self.from_chat, "name", "Unknown")

        timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(self.timestamp),
        )

        return (
            f"[Message]\n"
            f"  Direction : {direction}\n"
            f"  Chat      : {chat_name}\n"
            f"  Msg ID    : {self.message_id}\n"
            f"  Type      : {self.msgtype or 'text'}\n"
            f"  Encrypted : {self.is_encrypted()}\n"
            f"  Preview   : {preview}\n"
            f"  Time      : {timestamp}"
        )

    def __repr__(self) -> str:
        """Developer-friendly concise representation."""
        chat_name = getattr(self.from_chat, "name", "Unknown")

        return (
            f"Message(" f"id='{self.message_id}', " f"fromMe={self.fromMe}, " f"chat='{chat_name}')"
        )

    # -----------------------------

    def to_dict(self) -> dict:
        """Structured representation for storage/logging."""
        return {
            "id_serialized": self.id_serialized,
            "fromMe": self.fromMe,
            "chat": getattr(self.from_chat, "name", None),
            "msgtype": self.msgtype,
            "timestamp": self.timestamp,
            "encrypted": self.is_encrypted(),
        }
