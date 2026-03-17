"""WhatsApp media upload functionality."""

from __future__ import annotations

import asyncio
import logging
import random
import weakref
from pathlib import Path
from playwright.async_api import Page, Locator, FileChooser, TimeoutError as PlaywrightTimeoutError

from camouchat.Exceptions.whatsapp import MenuError, MediaCapableError, WhatsAppError
from camouchat.Interfaces.media_capable_interface import MediaCapableInterface, MediaType, FileTyped
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig


class MediaCapable(MediaCapableInterface):
    """Handles media file uploads to WhatsApp chats."""

    _instances: weakref.WeakKeyDictionary[Page, MediaCapable] = weakref.WeakKeyDictionary()
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> MediaCapable:
        page = kwargs.get("page") or (args[0] if args else None)
        if page is None:
            return super(MediaCapable, cls).__new__(cls)
        if page not in cls._instances:
            instance = super(MediaCapable, cls).__new__(cls)
            cls._instances[page] = instance
        return cls._instances[page]

    def __init__(self, page: Page, log: logging.Logger, UIConfig: WebSelectorConfig):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__(page=page, log=log, UIConfig=UIConfig)
        if self.page is None:
            raise ValueError("page must not be None")
        self._initialized = True

    async def menu_clicker(self) -> None:
        """Open the attachment menu."""
        try:
            menu_icon = await self.UIConfig.plus_rounded_icon().element_handle(timeout=1000)

            if not menu_icon:
                raise MenuError("Menu Locator return None/Empty / menu_clicker / MediaCapable")

            await menu_icon.click(timeout=3000)
            await asyncio.sleep(random.uniform(1.0, 1.5))

        except PlaywrightTimeoutError as e:
            await self.page.keyboard.press("Escape", delay=0.5)
            raise MediaCapableError("Time out while clicking menu") from e

    async def add_media(self, mtype: MediaType, file: FileTyped, **kwargs) -> bool:
        """Upload a media file to the current chat."""
        await self.menu_clicker()
        try:
            target = await self._getOperational(mtype=mtype)
            if not await target.is_visible(timeout=3000):
                raise MediaCapableError("Attach option not visible")

            async with self.page.expect_file_chooser() as fc:
                await target.click(timeout=3000)
            chooser: FileChooser = await fc.value

            p = Path(file.uri)
            if not p.exists() or not p.is_file():
                raise MediaCapableError(f"Invalid file path: {file.uri}")

            await chooser.set_files(str(p.resolve()))
            self.log.debug(f" --- Sent {str(p.resolve())} , [Mtype] = [{mtype}] ")
            return True

        except PlaywrightTimeoutError as e:
            raise MediaCapableError("Timeout while resolving media option") from e

        except WhatsAppError as e:
            if isinstance(e, MediaCapableError):
                raise e
            raise MediaCapableError("Unexpected Error in add_media") from e

    async def _getOperational(self, mtype: MediaType) -> Locator:
        """Get the appropriate menu locator for the media type."""
        sc = self.UIConfig
        if mtype in (MediaType.TEXT, MediaType.IMAGE, MediaType.VIDEO):
            return sc.photos_videos()

        if mtype == MediaType.AUDIO:
            return sc.audio()

        return sc.document()
