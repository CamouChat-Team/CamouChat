from typing import Any, Optional, Protocol

from .chat import ChatProtocol


class MessageProtocol(Protocol):
    """Message Interface Base Class — platform-agnostic."""

    timestamp: float | int | None
    body: str | None
    msgtype: Optional[str]
    from_chat: ChatProtocol | str
    ui: Optional[Any]  # Browser-specific; typed concretely in plugin (e.g. Playwright ElementHandle)
    id_serialized: Optional[str]
