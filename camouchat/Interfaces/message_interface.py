from abc import ABC
from typing import Optional, Union

from playwright.async_api import ElementHandle, Locator

from camouchat.Interfaces.chat_interface import ChatInterface


class MessageInterface(ABC):
    """Message Interface Base Class"""

    timestamp: float | int | None
    body: str | None
    msgtype: Optional[str]
    from_chat: ChatInterface | str
    ui: Optional[Union[ElementHandle, Locator]] = None
    id_serialized: Optional[str]
