from typing import Protocol
from playwright.async_api import ElementHandle, Locator


class ChatInterface(Protocol):
    """Chat Interface Base Class"""

    name: str | None
    id_serialized: str | None
    ui: Locator | ElementHandle | None = None
    timestamp: float | int | None
