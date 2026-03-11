"""Abstract base class for chat processors."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from playwright.async_api import Page

from src.Interfaces.chat_interface import ChatInterface
from src.WhatsApp.web_ui_config import WebSelectorConfig


class ChatProcessorInterface(ABC):
    """Base interface for chat fetching and management."""

    capabilities: Dict[str, bool]

    def __init__(
        self, log: logging.Logger, page: Page, UIConfig: WebSelectorConfig, **kwargs
    ) -> None:
        self.log = log
        self.page = page
        self.UIConfig = UIConfig

    @abstractmethod
    async def fetch_chats(self, **kwargs) -> List[ChatInterface]:
        """Fetch available chats from the UI."""
        ...

    @abstractmethod
    async def _click_chat(self, chat: Optional[ChatInterface], **kwargs) -> bool:
        """Click to open a chat."""
        ...

    @abstractmethod
    async def _get_Wrapped_Chat(self, **kwargs) -> List[ChatInterface]:
        """Extract and wrap chat elements."""
        ...
