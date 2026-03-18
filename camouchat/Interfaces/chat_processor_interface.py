"""Abstract base class for chat processors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger, LoggerAdapter
from typing import Dict, Optional, Sequence, Union

from playwright.async_api import Page

from camouchat.Interfaces.chat_interface import ChatInterface
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig
from camouchat.camouchat_logger import camouchatLogger


class ChatProcessorInterface(ABC):
    """Base interface for chat fetching and management."""

    capabilities: Dict[str, bool]

    def __init__(
        self,
        page: Page,
        ui_config: WebSelectorConfig,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
        **kwargs,
    ) -> None:
        self.log = log or camouchatLogger
        self.page = page
        self.UIConfig = ui_config

    @abstractmethod
    async def fetch_chats(self, **kwargs) -> Sequence[ChatInterface]:
        """Fetch available chats from the UI."""
        ...

    @abstractmethod
    async def _click_chat(self, chat: Optional[ChatInterface], **kwargs) -> bool:
        """Click to open a chat."""
        ...

    @abstractmethod
    async def _get_Wrapped_Chat(
        self, limit: int = 5, retry: int = 5, **kwargs
    ) -> Sequence[ChatInterface]:
        """Extract and wrap chat elements."""
        ...
