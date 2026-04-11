from typing import Optional, Union, Protocol

from playwright.async_api import ElementHandle, Locator

from camouchat.contracts.chat_interface import ChatInterface


class MessageInterface(Protocol):
    """Message Interface Base Class"""

    timestamp: float | int | None
    body: str | None
    msgtype: Optional[str]
    from_chat: ChatInterface | str
    ui: Optional[Union[ElementHandle, Locator]] = None
    id_serialized: Optional[str]
