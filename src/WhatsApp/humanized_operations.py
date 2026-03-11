"""Human-like typing simulation for WhatsApp input."""

from __future__ import annotations

import logging
import random
import asyncio
import os
import tempfile
from filelock import FileLock
from typing import Union, Optional

import pyperclip
from playwright.async_api import Page, ElementHandle, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from src.Exceptions.base import ElementNotFoundError, HumanizedOperationError
from src.Interfaces.humanize_operation_interface import HumanizeOperationInterface
from src.Interfaces.web_ui_selector import WebUISelectorCapable

_clipboard_async_lock = asyncio.Lock()

_lock_file_path = os.path.join(tempfile.gettempdir(), "whatsapp_clipboard.lock")
_clipboard_file_lock = FileLock(_lock_file_path)


class HumanizedOperations(HumanizeOperationInterface):
    """Simulates human-like typing with variable delays."""

    def __init__(self, page: Page, log: logging.Logger, UIConfig: WebUISelectorCapable):
        super().__init__(page=page, log=log, UIConfig=UIConfig)
        if self.page is None:
            raise ValueError("page must not be None")

    async def typing(self, text: str, **kwargs) -> bool:
        """
        Type text with human-like delays.

        :param text: Text to type
        Kwargs:
            source: Target element (ElementHandle or Locator)
        """
        source: Optional[Union[ElementHandle, Locator]] = kwargs.get("source") or None
        if not source:
            raise ElementNotFoundError("Source Element not found.")

        try:
            await source.click(timeout=3000)
            await source.press("Control+A")
            await source.press("Backspace")

            self.log.info(f"Cleared Previous text & Typing at source : {source}")

            lines = text.split("\n")

            if len(text) <= 50:
                await self.page.keyboard.type(text=text, delay=random.randint(80, 100))
            else:
                for i, line in enumerate(lines):
                    if len(line) > 50:
                        await self._safe_clipboard_paste(line)
                    else:
                        await self.page.keyboard.type(text=line, delay=random.randint(80, 100))

                    if i < len(lines) - 1:
                        await self.page.keyboard.press("Shift+Enter")
            return True
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            self.log.debug("Humanized typing failed, falling back to instant fill", exc_info=e)
            return await self._Instant_fill(text=text, source=source)

    async def _Instant_fill(
        self, text: str, source: Optional[Union[ElementHandle, Locator]]
    ) -> bool:
        """Fallback to instant fill when typing fails."""
        if not source:
            raise ElementNotFoundError("Source is Empty in _instant_fill.")

        try:
            await source.fill(text)
            await self.page.keyboard.press("Enter")
            return True
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            await self.page.keyboard.press("Escape", delay=0.5)
            await self.page.keyboard.press("Escape", delay=0.5)
            raise HumanizedOperationError(
                "Instant fill failed. Typing operation was not successful."
            ) from e

    async def _safe_clipboard_paste(self, text: str) -> None:
        """
        Safely copy text to OS clipboard and paste atomically.
        Prevents race conditions across and concurrent profiles.
        """

        loop = asyncio.get_running_loop()
        previous_clipboard: Optional[str] = None
        async with _clipboard_async_lock:
            # Acquire OS-level file lock in executor (blocking operation)
            await loop.run_in_executor(None, _clipboard_file_lock.acquire)

            try:
                # Get clipboard safely
                previous_clipboard = await loop.run_in_executor(None, pyperclip.paste)
                # Copy text safely
                await loop.run_in_executor(None, pyperclip.copy, text)

                # Small delay ensures clipboard propagation
                await asyncio.sleep(0.05)

                await self.page.keyboard.press("Control+V")
            finally:
                # Restore previous clipboard content
                if previous_clipboard is not None:
                    await loop.run_in_executor(None, pyperclip.copy, previous_clipboard)
                await loop.run_in_executor(None, _clipboard_file_lock.release)
