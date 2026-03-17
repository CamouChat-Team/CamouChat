"""WhatsApp Message Class contracted with Message Interface Template"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Union, Literal, Optional

from playwright.async_api import ElementHandle, Locator

from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.WhatsApp.models.chat import Chat


@dataclass
class Message(MessageInterface):
    """Represents a WhatsApp message entity with safe logging and structured metadata."""

    direction: Literal["in", "out"]
    data_id: str

    raw_data: str
    parent_chat: Chat
    message_ui: Optional[Union[ElementHandle, Locator]]

    data_type: Optional[str] = None
    message_id: str = field(init=False)
    system_hit_time: float = field(default_factory=time.time)

    # Encryption fields
    encrypted_message: Optional[str] = None
    encryption_nonce: Optional[str] = None

    encrypted_chat_name: Optional[str] = None
    chat_name_nonce: Optional[str] = None
    parent_chat_name_index: Optional[str] = None

    def __post_init__(self):
        self.message_id = self._message_key()

    def _message_key(self) -> str:
        return f"wa-msg::{self.data_id}"

    # -----------------------------

    def isIncoming(self) -> Optional[bool]:
        """Returns True if incoming, False if outgoing."""
        if self.direction == "in":
            return True
        if self.direction == "out":
            return False
        return None

    def is_encrypted(self) -> bool:
        """Check if message content is encrypted."""
        return self.encrypted_message is not None

    # -----------------------------

    def __str__(self) -> str:
        """User-friendly print (safe for logs, no sensitive leakage)."""

        direction = "IN" if self.direction == "in" else "OUT"

        # Safe preview (avoid dumping full message)
        preview = (self.raw_data or "").replace("\n", " ").strip()
        preview = preview[:50] + ("..." if len(preview) > 50 else "")

        chat_name = getattr(self.parent_chat, "chat_name", "Unknown")

        timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(self.system_hit_time),
        )

        return (
            f"[Message]\n"
            f"  Direction : {direction}\n"
            f"  Chat      : {chat_name}\n"
            f"  Msg ID    : {self.message_id}\n"
            f"  Type      : {self.data_type or 'text'}\n"
            f"  Encrypted : {self.is_encrypted()}\n"
            f"  Preview   : {preview}\n"
            f"  Time      : {timestamp}"
        )

    def __repr__(self) -> str:
        """Developer-friendly concise representation."""
        chat_name = getattr(self.parent_chat, "chat_name", "Unknown")

        return (
            f"Message("
            f"id='{self.message_id}', "
            f"dir='{self.direction}', "
            f"chat='{chat_name}')"
        )

    # -----------------------------

    def to_dict(self) -> dict:
        """Structured representation for storage/logging."""
        return {
            "message_id": self.message_id,
            "direction": self.direction,
            "chat": getattr(self.parent_chat, "chat_name", None),
            "data_type": self.data_type,
            "timestamp": self.system_hit_time,
            "encrypted": self.is_encrypted(),
        }
