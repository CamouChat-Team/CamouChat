"""Camoufox Browser integration"""

from __future__ import annotations

import os
from logging import Logger, LoggerAdapter
from typing import Optional, Dict, Union

import camoufox.exceptions
from browserforge.fingerprints import Fingerprint
from camoufox.async_api import AsyncCamoufox, launch_options
from playwright.async_api import Page, BrowserContext

from camouchat.BrowserManager import Platform
from camouchat.BrowserManager.browser_config import BrowserConfig
from camouchat.BrowserManager.profile_info import ProfileInfo
from camouchat.Exceptions.base import BrowserException
from camouchat.Interfaces.browser_interface import BrowserInterface


class CamoufoxBrowser(BrowserInterface):
    """
    Camoufox browser implementation with fingerprint support.

    Handles browser lifecycle, fingerprint loading, and retry logic for IP issues.
    Uses dependency injection for logging and fingerprint generation.
    """

    # handles Multiple Profiles to multi browser context handling
    Map: Dict[int, BrowserContext] = {}

    def __init__(
        self,
        config: BrowserConfig,
        profile: ProfileInfo,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
    ) -> None:
        """
        Initializes the Camoufox browser manager.

        Args:
            config: Browser configuration (locale, headless, proxy, geoip, etc.)
            profile: Profile information for session isolation and fingerprint persistence.
            log: Logger instance for audit and error tracking.
        """
        super().__init__(log=log)
        self.config = config
        self.profile = profile
        self.BrowserForge = config.fingerprint_obj
        self.browser: Optional[BrowserContext] = None

        if self.BrowserForge is None:
            raise BrowserException("BrowserForge is missing from the browser instance.")

        if self.profile.cache_dir is None:
            raise BrowserException("Cache dir path is missing from the browser instance.")

        if self.profile.fingerprint_path is None:
            raise BrowserException("Fingerprint path is missing from the browser instance.")

        if not self.config.headless:
            self.log.info(
                "Opening Browser into visible Mode. Change headless to True for Invisible Browser."
            )

    async def get_instance(self) -> BrowserContext:
        if self.browser is None:
            self.browser = await self.__GetBrowser__()
            pid = os.getpid()
            self.Map[pid] = self.browser
            self.profile.last_active_pid = pid  # in-memory snapshot in sync
        return self.browser

    async def __GetBrowser__(self, tries: int = 1) -> BrowserContext:
        """
        Internal method to launch the Camoufox browser with anti-detection enabled.

        Configures the browser with:
        - Persistent context (session isolation)
        - Fingerprint spoofing (from BrowserForge)
        - GeoIP spoofing (coordinates, timezone, language matching)
        - Proxy configuration (residential proxies recommended)
        - Humanization (smooth mouse movements)
        - DOM caching (optional)

        Args:
            tries: Current retry attempt number (max 5).

        Returns:
            The launched Playwright BrowserContext.

        Raises:
            BrowserException: If the browser fails to launch or IP is rejected after max tries.
        """
        if self.browser is not None:
            return self.browser

        if tries > 5:
            raise BrowserException("Max Camoufox IP retry attempts exceeded")

        fg: Fingerprint = self.BrowserForge.get_fg(profile=self.profile)

        try:
            browser = await AsyncCamoufox(
                **launch_options(
                    locale=self.config.locale,
                    headless=self.config.headless,
                    humanize=True,
                    geoip=self.config.geoip,
                    proxy=self.config.proxy,
                    fingerprint=fg,
                    enable_cache=self.config.enable_cache,
                    i_know_what_im_doing=True,
                    firefox_user_prefs=self.config.prefs if self.config.prefs else None,
                    main_world_eval=True,
                ),
                persistent_context=True,
                user_data_dir=self.profile.cache_dir,
            ).__aenter__()

            self.browser = browser  # type: ignore[assignment]
            return self.browser  # type: ignore[return-value]

        except camoufox.exceptions.InvalidIP:
            self.log.warning(f"Camoufox IP failed (attempt {tries}/5). Retrying...")
            return await self.__GetBrowser__(tries=tries + 1)

        except Exception as e:
            raise BrowserException("Failed to launch Camoufox browser") from e

    async def get_page(self, platform: Platform) -> Page:
        """
        Returns an available blank page if one exists,
        otherwise creates and returns a new page.
        Automatically initializes the browser if needed.

        **kwargs :
            platform : Platform =  patches page according to the platform given.
        """
        browser = self.browser
        if browser is None:
            browser = await self.get_instance()

        # Reuse an existing blank page if possible
        for page in browser.pages:
            try:
                if page.url == "about:blank" and not page.is_closed():
                    js_path = os.path.join(os.path.dirname(__file__), "wa-js", "wppconnect-wa.js")
                    await page.add_init_script(path=js_path)
                    return page
            except Exception as e:
                self.log.warning(f"Error checking page state: {e}")

        # Otherwise create a new page
        try:
            page: Page = await browser.new_page()
            js_path = os.path.join(os.path.dirname(__file__), "wa-js", "wppconnect-wa.js")
            await page.add_init_script(path=js_path)
            return page
        except Exception as e:
            self.log.error("Failed to create new page", exc_info=True)
            raise BrowserException("Could not create a new page") from e

    @classmethod
    async def close_browser_by_pid(cls, pid: int) -> bool:
        browser = cls.Map.get(pid)
        if not browser:
            return True

        try:
            await browser.__aexit__(None, None, None)
            cls.Map.pop(pid, None)
            return True
        except Exception:
            return False
