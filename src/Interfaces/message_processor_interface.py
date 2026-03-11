"""Abstract base class for message processors."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from playwright.async_api import Page

from src.Interfaces.storage_interface import StorageInterface
from src.Interfaces.message_interface import MessageInterface
from src.FIlter.message_filter import MessageFilter
from src.Interfaces.chat_interface import ChatInterface
from src.WhatsApp.web_ui_config import WebSelectorConfig


class MessageProcessorInterface(ABC):
    """Base interface for message extraction and processing."""

    def __init__(
        self,
        log: logging.Logger,
        page: Page,
        UIConfig: WebSelectorConfig,
        storage_obj: Optional[StorageInterface] = None,
        filter_obj: Optional[MessageFilter] = None,
    ):
        self.storage = storage_obj
        self.filter = filter_obj
        self.log = log
        self.page = page
        self.UIConfig = UIConfig

    @abstractmethod
    async def _get_wrapped_Messages(self, retry: int, *args, **kwargs) -> List[MessageInterface]:
        """Extract and wrap messages from UI elements."""
        ...

    @abstractmethod
    async def Fetcher(
        self, chat: ChatInterface, retry: int, *args, **kwargs
    ) -> List[MessageInterface]:
        """Fetch messages from a chat with storage and filtering."""
        ...
