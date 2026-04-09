"""WhatsApp media upload and download functionality."""

from __future__ import annotations

import asyncio
import random
import re
import weakref
from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Any, Dict, Optional, Union

from playwright.async_api import (
    Page,
    Locator,
    FileChooser,
    TimeoutError as PlaywrightTimeoutError,
)

from camouchat.BrowserManager.profile_info import ProfileInfo
from camouchat.Exceptions.whatsapp import MenuError, MediaCapableError, WhatsAppError
from camouchat.Interfaces.media_capable_interface import (
    MediaCapableInterface,
    MediaType,
    FileTyped,
)
from camouchat.WhatsApp.api import WapiSession
from camouchat.WhatsApp.api.models import MessageModelAPI
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig

# ── Media-type → category bucket ──────────────────────────────────────────────
_WA_TYPE_TO_CATEGORY: Dict[str, str] = {
    "image": "image",
    "sticker": "image",
    "video": "video",
    "gif": "video",
    "audio": "audio",
    "ptt": "audio",
    "document": "document",
    "vcard": "document",
    "product": "document",
}

# Category → ProfileInfo attribute name for the save directory
_CATEGORY_TO_PROFILE_ATTR: Dict[str, str] = {
    "image": "media_images_dir",
    "video": "media_videos_dir",
    "audio": "media_voice_dir",
    "document": "media_documents_dir",
}


class MediaCapable(MediaCapableInterface[WebSelectorConfig]):
    """Handles media file uploads and downloads for WhatsApp chats.

    Upload (add_media):
        Works standalone — no wapi or profile required.

    Download (save_media):
        Requires both ``wapi`` (a started WapiSession) and ``profile``
        (a ProfileInfo instance) injected at construction time.
        Uses Cache API only — no CDN/network calls from our side.
        Retries every second until WA's render cycle caches the blob.
    """

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

    def __init__(
        self,
        page: Page,
        UIConfig: WebSelectorConfig,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
        wapi: Optional[WapiSession] = None,
        profile: Optional[ProfileInfo] = None,
    ):
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__(page=page, log=log, UIConfig=UIConfig)
        if self.page is None:
            raise ValueError("page must not be None")
        self._wapi: Optional[WapiSession] = wapi
        self._profile: Optional[ProfileInfo] = profile
        self._initialized = True

    # ─────────────────────────────────────────────────────────────────────────
    # UPLOAD
    # ─────────────────────────────────────────────────────────────────────────

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
        force = kwargs.get("force", False)
        await self.menu_clicker()
        self.log.debug("Menu Clicked, Now Checking for corret DataType Locator")
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
            if force:
                await asyncio.sleep(random.uniform(0.6, 1.0))
                try:
                    send_btn = self.page.get_by_role("button", name=re.compile(r"send", re.I)).last
                    await send_btn.click(timeout=4000)
                    self.log.debug("Media preview send button clicked.")
                except Exception:
                    # Fallback: simple Enter key press if button not found
                    await self.page.keyboard.press("Enter")
                    self.log.debug("Media preview closed via Enter key.")

            self.log.info(f" --- Sent {str(p.resolve())} , [Mtype] = [{mtype}] ")
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
            self.log.debug("photo&Video locator selected")
            return sc.photos_videos()

        if mtype == MediaType.AUDIO:
            self.log.debug("Audio locator selected")
            return sc.audio()

        self.log.debug("Document locator selected")
        return sc.document()

    # ─────────────────────────────────────────────────────────────────────────
    # DOWNLOAD
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_save_dir(self, wa_type: Optional[str]) -> Path:
        """Map a WhatsApp MsgType string to the correct ProfileInfo directory."""
        if self._profile is None:
            raise MediaCapableError(
                "save_media requires a ProfileInfo instance. "
                "Pass profile=<ProfileInfo> when constructing MediaCapable."
            )
        category = _WA_TYPE_TO_CATEGORY.get(wa_type or "", "document")
        attr = _CATEGORY_TO_PROFILE_ATTR[category]
        return getattr(self._profile, attr)

    async def save_media(
        self,
        message: MessageModelAPI,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Download and save media from a MessageModelAPI message — Cache API only.

        When open_chat renders the chat, WhatsApp Web downloads the encrypted
        media blob into the browser Cache API as part of its normal render cycle.
        This method retries the cache lookup every second for up to poll_secs
        seconds — zero CDN calls, zero network requests from our side.

        Args:
            message:   MessageModelAPI with MsgType, directPath, mediaKey.
            filename:  Optional filename override (basename, no directory).
                       If None, auto-generated as <type>_<safe_id><ext>.
            poll_secs: Max seconds to wait for WA to cache the blob (default 15).
                       Set to 1 to try exactly once without retrying.

        Returns:
            Absolute path string on success, or None if blob did not appear
            in cache within the poll window.

        Raises:
            MediaCapableError: If wapi or profile were not injected.
        """
        if self._wapi is None:
            raise MediaCapableError(
                "save_media requires a WapiSession. "
                "Pass wapi=<WapiSession> (after .start()) when constructing MediaCapable."
            )

        wa_type = message.MsgType or ""
        category = _WA_TYPE_TO_CATEGORY.get(wa_type, "document")
        save_dir = self._resolve_save_dir(wa_type)
        save_dir.mkdir(parents=True, exist_ok=True)

        raw: Dict[str, Any] = {
            "type": wa_type,
            "directPath": message.directPath,
            "mediaKey": message.mediaKey,
            "id_serialized": message.id_serialized,
            "mimetype": message.mimetype,
            "viewOnce": message.isViewOnce or False,
        }

        # Debug: dump raw media fields so we can verify what arrived from JS bridge
        self.log.debug(
            f"[save_media] raw fields — "
            f"directPath={message.directPath!r} "
            f"mediaKey={'<set>' if message.mediaKey else None!r} "
            f"mimetype={message.mimetype!r} "
            f"id={message.id_serialized!r}"
        )

        save_path = (
            str(save_dir / filename)
            if filename
            else self._wapi.bridge.media_save_path(raw, str(save_dir))
        )

        # Simplified: WPP's downloadMedia handles local cache (LRU) transparently.
        # If auto-download is ON, this call is zero-CDN (stealth).
        path = await self._wapi.bridge.extract_media(
            message=raw,
            save_path=save_path,
        )

        self.log.debug(f"[save_media] type={wa_type!r} category={category!r} path={path!r}")
        return path
