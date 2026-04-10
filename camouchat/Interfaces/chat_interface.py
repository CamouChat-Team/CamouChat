from abc import ABC

from playwright.async_api import ElementHandle, Locator


class ChatInterface(ABC):
    """Chat Interface Base Class"""

    name: str | None
    id_serialized: str | None
    ui: Locator | ElementHandle | None = None
    timestamp: float | int | None
