"""Abstract base class for message processors."""

from __future__ import annotations

from logging import Logger, LoggerAdapter
from camouchat.camouchat_logger import camouchatLogger
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Union

from playwright.async_api import Page

from camouchat.Interfaces.storage_interface import StorageInterface
from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.Filter.message_filter import MessageFilter
from camouchat.Interfaces.chat_interface import ChatInterface
from camouchat.Interfaces.web_ui_selector import WebUISelectorCapable

T = TypeVar("T", bound=MessageInterface)
U = TypeVar("U", bound=WebUISelectorCapable)


class MessageProcessorInterface(ABC, Generic[T, U]):
    """Base interface for message extraction and processing."""

    UIConfig: Optional[U] = None

    def __init__(
        self,
        page: Optional[Page] = None,
        UIConfig: Optional[U] = None,
        storage_obj: Optional[StorageInterface] = None,
        filter_obj: Optional[MessageFilter] = None,
        log: Optional[Union[LoggerAdapter, Logger]] = None,
    ):
        from camouchat.NoOpPattern import NoOpStorage, NoOpMessageFilter

        self.storage = storage_obj or NoOpStorage()
        self.filter = filter_obj or NoOpMessageFilter()
        self.log = log or camouchatLogger
        self.page = page
        self.UIConfig = UIConfig

    @abstractmethod
    async def fetch_messages(self, chat: ChatInterface, retry: int, **kwargs) -> List[T]:
        """Fetch messages from a chat with storage and filtering."""
        ...
