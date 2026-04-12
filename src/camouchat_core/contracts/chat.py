from typing import Any, Optional, Protocol


class ChatProtocol(Protocol):
    """Chat Interface Base Class — platform-agnostic."""

    name: str | None
    id_serialized: str | None
    ui: Optional[Any]  # Browser-specific; typed concretely in plugin
    timestamp: float | int | None
