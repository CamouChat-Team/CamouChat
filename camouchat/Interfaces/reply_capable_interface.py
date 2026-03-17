"""Abstract base class for reply functionality."""

from logging import Logger, LoggerAdapter
from camouchat.camouchat_logger import camouchatLogger
from abc import ABC, abstractmethod
from typing import Optional, Union

from playwright.async_api import Page

from camouchat.Interfaces.humanize_operation_interface import HumanizeOperationInterface
from camouchat.Interfaces.message_interface import MessageInterface
from camouchat.Interfaces.web_ui_selector import WebUISelectorCapable


class ReplyCapableInterface(ABC):
    """Base interface for message reply operations."""

    def __init__(
        self, page: Page,  ui_config: WebUISelectorCapable,log: Optional[Union[Logger,LoggerAdapter]], **kwargs
    ) -> None:
        self.page = page
        self.log = log or camouchatLogger
        self.UIConfig = ui_config

    @abstractmethod
    async def reply(
        self,
        Message: MessageInterface,
        humanize: HumanizeOperationInterface,
        text: Optional[str],
        **kwargs,
    ) -> bool:
        """Send a reply to a message."""
        ...
