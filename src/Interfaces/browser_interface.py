"""
Browser abstraction interface.

Defines the core contract for browser lifecycle management.
Any browser implementation (Camoufox, Playwright, etc.) must implement this.
"""

from abc import ABC, abstractmethod

from playwright.async_api import BrowserContext, Page


class BrowserInterface(ABC):
    """
    Base interface for browser operations.

    Implementations handle browser initialization, page management, and cleanup.
    """

    @abstractmethod
    async def get_instance(self) -> BrowserContext:
        """Get or create the browser context instance."""
        ...

    @classmethod
    @abstractmethod
    async def close_browser_by_pid(cls, pid: int) -> bool:
        """Close the browser context by process ID. Returns True if successful."""
        ...

    @abstractmethod
    async def get_page(self) -> Page:
        """Get an available page or create a new one."""
        ...
