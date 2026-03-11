"""
This is an ChatInterFace to implement and usage
for every Platform Chat Based Objects.
"""

from __future__ import annotations

from typing import Optional, Protocol, Union

from playwright.async_api import ElementHandle, Locator


class ChatInterface(Protocol):
    """Chat Interface,"""

    chat_name: str
    chat_id: str
    chat_ui: Optional[Union[Locator, ElementHandle]]
    System_Hit_Time: float

    def _chat_key(self, **kwargs) -> str: ...
