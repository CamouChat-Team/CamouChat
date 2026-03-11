"""Message Interface Protocol, Every Message Class have to Implement this interface"""

from typing import Protocol, Optional, Union

from playwright.async_api import ElementHandle, Locator

from src.Interfaces.chat_interface import ChatInterface


class MessageInterface(Protocol):
    """Message Interface Protocol, Every Message Class have to Implement this interface"""

    system_hit_time: float
    raw_data: str
    data_type: Optional[str]
    parent_chat: ChatInterface
    message_ui: Optional[Union[ElementHandle, Locator]]
    message_id: Optional[str]

    def _message_key(self) -> str: ...
