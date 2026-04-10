"""
WhatsApp Chat contracted with ChatInterface Template
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, Union

from playwright.async_api import ElementHandle, Locator

from camouchat.Interfaces.chat_interface import ChatInterface


@dataclass
class Chat(ChatInterface):
    name: str
    ui: Optional[Union[ElementHandle, Locator]]
    id_serialized: str = field(init=False)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        self.id_serialized = self._chat_key()

    def _chat_key(self) -> str:
        return f"wa::{self.name.lower().strip()}"

    def __str__(self) -> str:
        return (
            f"[WhatsAppChat]\n"
            f"  Name : {self.name}\n"
            f"  ID   : {self.id_serialized}\n"
            f"  Time : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}"
        )

    def __repr__(self) -> str:
        return f"whatsapp_chat(name='{self.name}', id_serialized='{self.id_serialized}')"
