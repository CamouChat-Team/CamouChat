"""Abstract base class for login handlers."""
import logging
from abc import ABC, abstractmethod

from playwright.async_api import Page

from src.Interfaces.web_ui_selector import WebUISelectorCapable


class LoginInterface(ABC):
    """Base interface for authentication handlers."""

    def __init__(self, page: Page, UIConfig: WebUISelectorCapable, log: logging.Logger | logging.LoggerAdapter) :
        self.page = page
        self.UIConfig = UIConfig
        self.log = log

    @abstractmethod
    async def login(self, **kwargs) -> bool:
        """Perform login authentication."""
        ...

    async def logout(self, **kwargs) -> bool:
        """Perform logout and cleanup."""
        ...

    async def is_login_successful(self, **kwargs) -> bool:
        """Check if login was successful."""
        ...
