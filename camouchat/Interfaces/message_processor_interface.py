"""Abstract base class for message processors."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar

from playwright.async_api import Page

from camouchat.Interfaces.storage_interface import StorageInterface
from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.Filter.message_filter import MessageFilter
from camouchat.Interfaces.chat_interface import ChatInterface
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig

T = TypeVar("T", bound=MessageInterface)


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
    async def _get_wrapped_Messages(self, retry: int,  **kwargs) -> List[T]:
        """Extract and wrap messages from UI elements."""
        ...

    @abstractmethod
    async def fetch_messages(self, chat: ChatInterface, retry: int,  **kwargs) -> List[T]:
        """Fetch messages from a chat with storage and filtering."""
        ...
