"""All the Humanized Operation Interface modules"""

from abc import ABC, abstractmethod

from playwright.async_api import Page
import logging

from src.Interfaces.web_ui_selector import WebUISelectorCapable


class HumanizeOperationInterface(ABC):
    """
    All Humanized Altered Operation here.
    """

    @abstractmethod
    def __init__(
        self, page: Page, log: logging.Logger, UIConfig: WebUISelectorCapable, **kwargs
    ) -> None:
        self.page = page
        self.log = log
        self.UIConfig = UIConfig

    @abstractmethod
    async def typing(self, text: str, **kwargs) -> bool: ...
