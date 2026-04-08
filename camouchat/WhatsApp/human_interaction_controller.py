"""Human-like typing simulation for WhatsApp input."""

from __future__ import annotations

import asyncio
import os
import random
import tempfile
import weakref
from logging import Logger, LoggerAdapter
from typing import Union, Optional

import pyperclip
from filelock import FileLock
from playwright.async_api import Page, ElementHandle, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from camouchat.WhatsApp.api import WapiWrapper

from camouchat.Exceptions.base import ElementNotFoundError, HumanizedOperationError
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig
from camouchat.camouchat_logger import camouchatLogger
from camouchat.WhatsApp.api.wa_js.wajs_scripts import WAJS_Scripts

_clipboard_async_lock = asyncio.Lock()

_lock_file_path = os.path.join(tempfile.gettempdir(), "whatsapp_clipboard.lock")
_clipboard_file_lock = FileLock(_lock_file_path)


class HumanInteractionController:
    """Simulates human-like typing with variable delays."""

    _instances: weakref.WeakKeyDictionary[Page, HumanInteractionController] = (
        weakref.WeakKeyDictionary()
    )
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> HumanInteractionController:
        page = kwargs.get("page") or (args[0] if args else None)
        if page is None:
            return super(HumanInteractionController, cls).__new__(cls)
        if page not in cls._instances:
            instance = super(HumanInteractionController, cls).__new__(cls)
            cls._instances[page] = instance
        return cls._instances[page]

    def __init__(
        self,
        page: Page,
        ui_config: WebSelectorConfig,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
    ) -> None:

        if hasattr(self, "_initialized") and self._initialized:
            return

        self.page = page
        self.ui_config = ui_config
        self.log = log or camouchatLogger
        if self.page is None:
            raise ValueError("page must not be None")

        self._initialized = True

    async def typing(self, text: str, **kwargs) -> bool:
        """
        Type text with human-like delays.

        :param text: Text to type
        Kwargs:
            source: Target element (ElementHandle or Locator)
        """
        source: Optional[Union[ElementHandle, Locator]] = kwargs.get("source")

        if not source:
            raise ElementNotFoundError("Source Element not found.")

        try:
            await self._ensure_clean_input(source)

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
            self.log.debug("Typing failed → fallback to instant fill", exc_info=e)
            return await self._Instant_fill(text=text, source=source)

    async def _ensure_clean_input(
        self, source: Union[ElementHandle, Locator], retries: int = 3
    ) -> None:

        for attempt in range(1, retries + 1):
            try:
                text = await source.inner_text()

                if text:
                    await source.click(timeout=3000)
                    await source.press("Control+A")
                    await source.press("Backspace")

                    self.log.debug(f"Cleared stale input: {text[:30]}")

                return

            except (PlaywrightTimeoutError, PlaywrightError):
                if attempt < retries:
                    await asyncio.sleep(0.2 * attempt)
                else:
                    self.log.warning("Failed to clear input after retries")
                    raise

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

    async def send_api_text(self, bridge: WapiWrapper, text: str, chat_id: str) -> bool:
        """
        Skips native OS usage & Directly send text via RAM Func.
        Initially supported for direct text msg sending only & works for Qouted Replies also.
        Dont support to send text with Media or other attachments.

        Gives Telementry : mouse moves , msg box click & focus , for txt len > 50 chars , add ctrl C & ctrl V telementry.
        Args :
            bridge : WapiWrapper instance
            text : Text to be sent
        Returns:
            bool: True if text is sent successfully.
        """

        if bridge is None:
            raise ValueError(
                "bridge is not given consider giving WapiSession'bridge or WapiWrapper"
            )

        try:
            inputBox = self.ui_config.message_box()
            await inputBox.click(timeout=5000)  # Telementry

            if not chat_id:
                raise HumanizedOperationError("Could not determine active chat ID from bridge.")

            await bridge._evaluate_stealth(f"wpp.chat.markIsComposing('{chat_id}', 3000)")

            if len(text) > 50:  # Telementry
                await self.page.keyboard.press("Control+C")
                await asyncio.sleep(random.uniform(0.05, 0.15))
                await self.page.keyboard.press("Control+V")

            await asyncio.sleep(random.uniform(1.2, 2.5))
            await bridge._evaluate_stealth(WAJS_Scripts.send_text_message(chat_id, text))
            return True

        except Exception as e:
            self.log.error(f"[HumanInteractionController] send_api_text failed: {e}")
            raise HumanizedOperationError(f"Failed to execute send_api_text: {e}") from e
