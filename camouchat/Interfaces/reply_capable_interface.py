"""Abstract base class for reply functionality."""

from logging import Logger, LoggerAdapter
from camouchat.camouchat_logger import camouchatLogger
from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, Union

from playwright.async_api import Page

from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.Interfaces.web_ui_selector import WebUISelectorCapable

M = TypeVar("M", bound=MessageInterface)
H = TypeVar("H")
U = TypeVar("U", bound=WebUISelectorCapable)


class ReplyCapableInterface(ABC, Generic[M, H, U]):
    """Base interface for message reply operations."""

    UIConfig: U

    def __init__(
        self,
        page: Page,
        ui_config: U,
        log: Optional[Union[Logger, LoggerAdapter]],
        **kwargs,
    ) -> None:
        self.page = page
        self.log = log or camouchatLogger
        self.UIConfig = ui_config

    @abstractmethod
    async def reply(
        self,
        message: M,
        humanize: H,
        text: Optional[str],
        **kwargs,
    ) -> bool:
        """Send a reply to a message."""
        ...
