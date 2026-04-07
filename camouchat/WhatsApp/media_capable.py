"""WhatsApp media upload and download functionality."""

from __future__ import annotations

import asyncio
import random
import weakref
from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Any, Dict, Optional, Union

from playwright.async_api import Page, Locator, FileChooser, TimeoutError as PlaywrightTimeoutError

from camouchat.BrowserManager.profile_info import ProfileInfo
from camouchat.Exceptions.whatsapp import MenuError, MediaCapableError, WhatsAppError
from camouchat.Interfaces.media_capable_interface import MediaCapableInterface, MediaType, FileTyped
from camouchat.WhatsApp.api import WapiSession
from camouchat.WhatsApp.api.models import MessageModelAPI
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig


# ── Media-type → category bucket ──────────────────────────────────────────────
# WhatsApp raw MsgModel `type` strings mapped to the 4 canonical categories
# that align with ProfileInfo directory attributes.
_WA_TYPE_TO_CATEGORY: Dict[str, str] = {
    # Images
    "image":    "image",
    "sticker":  "image",
    # Videos
    "video":    "video",
    "gif":      "video",
    # Audio / Voice
    "audio":    "audio",
    "ptt":      "audio",   # push-to-talk voice note
    # Documents / everything else
    "document": "document",
    "vcard":    "document",
    "product":  "document",
}

# Category → ProfileInfo attribute name for the save directory
_CATEGORY_TO_PROFILE_ATTR: Dict[str, str] = {
    "image":    "media_images_dir",
    "video":    "media_videos_dir",
    "audio":    "media_voice_dir",
    "document": "media_documents_dir",
}


class MediaCapable(MediaCapableInterface[WebSelectorConfig]):
    """Handles media file uploads and downloads for WhatsApp chats.

    Upload (add_media):
        Works standalone — no wapi or profile required.

    Download (save_media):
        Requires both ``wapi`` (a started WapiSession) and ``profile``
        (a ProfileInfo instance) to be injected at construction time.
        If either is absent, save_media raises MediaCapableError immediately.

        Discovery order for save directories::

            MessageModelAPI.MsgType
                → _WA_TYPE_TO_CATEGORY   (image / video / audio / document)
                → ProfileInfo.<dir_attr>  (media_images_dir / media_videos_dir / …)

        Download strategy (delegated to WapiWrapper.extract_media):
            1. Browser Cache API — zero network cost.
            2. CDN download via wpp.chat.downloadMedia() — network fallback.
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

    # ─────────────────────────────────────────────────────────────────────────
    # DOWNLOAD
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_save_dir(self, wa_type: Optional[str]) -> Path:
        """
        Map a WhatsApp MsgType string to the correct ProfileInfo directory.

        Args:
            wa_type: The raw ``MsgType`` from ``MessageModelAPI``
                     (e.g. ``'image'``, ``'ptt'``, ``'document'``).

        Returns:
            Absolute ``Path`` to the save directory.

        Raises:
            MediaCapableError: If ``profile`` was not injected.
        """
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
        Download and save the media attached to a ``MessageModelAPI`` message.

        .. note::
            **Requires WapiSession** — ``save_media`` is only available when
            both ``wapi`` (a started ``WapiSession``) and ``profile``
            (a ``ProfileInfo`` instance) were injected at construction time.
            Upload (``add_media``) works without them.

        **RAM-only — no CDN fallback.**  Only the browser Cache API is used.
        If WhatsApp has not yet written the media blob to the local cache
        (e.g. large files on a slow connection), this will return ``None``.
        CDN download (``WapiWrapper.extract_media_cdn``) exists but is
        deliberately not called here to avoid Meta's server-side access logs.

        Classification (4 buckets → 4 ``ProfileInfo`` directories):

        +-------------------+------------------+-------------------------------+
        | WA MsgType(s)     | Category         | ProfileInfo dir attr          |
        +===================+==================+===============================+
        | image, sticker    | image            | media_images_dir              |
        +-------------------+------------------+-------------------------------+
        | video, gif        | video            | media_videos_dir              |
        +-------------------+------------------+-------------------------------+
        | audio, ptt        | audio            | media_voice_dir               |
        +-------------------+------------------+-------------------------------+
        | document, vcard,  | document         | media_documents_dir           |
        | product, (others) |                  |                               |
        +-------------------+------------------+-------------------------------+

        Args:
            message:  A ``MessageModelAPI`` instance.  Must carry
                      ``MsgType``, ``directPath``, and ``mediaKey``
                      (all populated by ``from_dict`` from the JS bridge).
            filename: Optional filename override (basename only, no directory).
                      If ``None``, auto-generated as ``<type>_<safe_id><ext>``.

        Returns:
            Absolute path string of the saved file on success.

            ``None`` if extraction failed, which means one of:
                - ``directPath`` missing (message has no downloadable attachment).
                - ``mediaKey`` missing (cannot decrypt the blob).
                - Browser Cache API returned nothing (blob not cached yet).
                - Any unexpected JS / decode / IO error.

        Raises:
            MediaCapableError: If ``wapi`` or ``profile`` were not injected.
        """
        if self._wapi is None:
            raise MediaCapableError(
                "save_media requires a WapiSession. "
                "Pass wapi=<WapiSession> (after .start()) when constructing MediaCapable."
            )

        wa_type  = message.MsgType or ""
        category = _WA_TYPE_TO_CATEGORY.get(wa_type, "document")
        save_dir = self._resolve_save_dir(wa_type)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Build the raw dict that WapiWrapper.extract_media expects
        raw: Dict[str, Any] = {
            "type":          wa_type,
            "directPath":    message.directPath,
            "mediaKey":      message.mediaKey,
            "id_serialized": message.id_serialized,
            "mimetype":      message.mimetype,
            "viewOnce":      message.isViewOnce or False,
        }

        # Auto-generate filename if not supplied
        if filename:
            save_path = str(save_dir / filename)
        else:
            save_path = self._wapi.bridge.media_save_path(raw, str(save_dir))

        # RAM-only extraction — returns the saved path or None on any failure
        path = await self._wapi.bridge.extract_media(
            message=raw,
            save_path=save_path,
        )

        self.log.debug(
            f"[save_media] type={wa_type!r} category={category!r} path={path!r}"
        )
        return path

