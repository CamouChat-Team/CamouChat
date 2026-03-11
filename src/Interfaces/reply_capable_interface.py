"""Abstract base class for reply functionality."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from playwright.async_api import Page

from src.Interfaces.humanize_operation_interface import HumanizeOperationInterface
from src.Interfaces.message_interface import MessageInterface
from src.Interfaces.web_ui_selector import WebUISelectorCapable


class ReplyCapableInterface(ABC):
    """Base interface for message reply operations."""

    def __init__(
        self, page: Page, log: logging.Logger, UIConfig: WebUISelectorCapable, **kwargs
    ) -> None:
        self.page = page
        self.log = log
        self.UIConfig = UIConfig

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
