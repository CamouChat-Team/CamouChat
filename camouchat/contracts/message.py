from typing import Optional, Union, Protocol

from playwright.async_api import ElementHandle, Locator

from camouchat.contracts.chat import ChatProtocol


class MessageProtocol(Protocol):
    """Message Interface Base Class"""

    timestamp: float | int | None
    body: str | None
    msgtype: Optional[str]
    from_chat: ChatProtocol | str
    ui: Optional[Union[ElementHandle, Locator]] = None
    id_serialized: Optional[str]
