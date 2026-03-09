"""Camoufox Browser integration """
from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Union, Any
from logging import Logger, LoggerAdapter

import camoufox.exceptions
from browserforge.fingerprints import Fingerprint
from camoufox.async_api import AsyncCamoufox, launch_options
from playwright.async_api import Page, BrowserContext

from src.custom_logger import TweakioLogger
from src.BrowserManager.profile_info import ProfileInfo
from src.Exceptions.base import BrowserException
from src.Interfaces.browser_interface import BrowserInterface
from src.BrowserManager.browser_config import BrowserConfig



class CamoufoxBrowser(BrowserInterface):
    """
    Camoufox browser implementation with fingerprint support.

    Handles browser lifecycle, fingerprint loading, and retry logic for IP issues.
    Uses dependency injection for logging and fingerprint generation.
    """
    # handles Multiple Profiles to multi browser context handling
    Map : Dict[int , BrowserContext] = {}

    def __init__(

            self,
            config : BrowserConfig,
            profileInfo : ProfileInfo,
            log: Optional[Union[Logger, LoggerAdapter]] = None

    ) -> None:
        """
        :param config: BrowserConfig object
        :param profileInfo: ProfileInfo object
        :param log: obj of logging (Optional: if None, TweakioLogger is used)
        """
        self.config = config
        self.profileInfo = profileInfo
        self.BrowserForge = config.fingerprint_obj # streamline the same flow
        self.browser: Optional[BrowserContext] = None
        self.log: Union[Logger, LoggerAdapter]
        
        # Use provided logger or get specialized browser logger
        if log is None:
            self.log = TweakioLogger.get_logger("tweakio.browser", log_type="browser")
        else:
            self.log = log

        if self.BrowserForge is None:
            raise BrowserException("BrowserForge is missing from the browser instance.")

        if self.profileInfo.cache_dir is None:
            raise BrowserException("Cache dir path is missing from the browser instance.")

        if self.profileInfo.fingerprint_path is None:
            raise BrowserException("Fingerprint path is missing from the browser instance.")

        if not self.config.headless:
            self.log.info("Opening Browser into visible Mode. Change headless to True for Invisible Browser.")

    async def get_instance(self) -> BrowserContext:
        if self.browser is None:
            self.browser = await self.__GetBrowser__()
            pid = os.getpid()
            self.Map[pid] = self.browser
            self.profileInfo.last_active_pid = pid  # keep in-memory snapshot in sync
        return self.browser

    async def __GetBrowser__(self, tries: int = 1) -> BrowserContext:
        if self.browser is not None:
            return self.browser

        if tries > 5:
            raise BrowserException("Max Camoufox IP retry attempts exceeded")

        fg: Fingerprint = self.BrowserForge.get_fg(
            profile_path=self.profileInfo.fingerprint_path
        )

        try:
            self.browser = await AsyncCamoufox(
                **launch_options(
                    locale=self.config.locale,
                    headless=self.config.headless,
                    humanize=True,
                    geoip=True,
                    fingerprint=fg,
                    enable_cache=self.config.enable_cache,
                    i_know_what_im_doing=True,
                    firefox_user_prefs=self.config.prefs if self.config.prefs else None,
                    main_world_eval=True,
                ),
                persistent_context=True,
                user_data_dir=self.profileInfo.cache_dir,
            ).__aenter__()

            return self.browser

        except camoufox.exceptions.InvalidIP:
            self.log.warning(
                f"Camoufox IP failed (attempt {tries}/5). Retrying..."
            )
            return await self.__GetBrowser__(tries=tries + 1)

        except Exception as e:
            raise BrowserException("Failed to launch Camoufox browser") from e

    async def get_page(self) -> Page:
        """
        Returns an available blank page if one exists,
        otherwise creates and returns a new page.
        Automatically initializes the browser if needed.
        """
        browser = self.browser
        if browser is None:
            browser = await self.get_instance()

        # Reuse an existing blank page if possible
        for page in browser.pages:
            try:
                if page.url == "about:blank" and not page.is_closed():
                    return page
            except Exception as e:
                self.log.warning(f"Error checking page state: {e}")

        # Otherwise create a new page
        try:
            return await browser.new_page()
        except Exception as e:
            self.log.error("Failed to create new page", exc_info=True)
            raise BrowserException("Could not create a new page") from e

    async def close_browser(self) -> bool:
        """Close the browser context. Returns True if successful."""
        if self.browser is None:
            return True
        try:
            pid = os.getpid()
            await self.browser.__aexit__(None, None, None)
            self.Map.pop(pid, None)
            self.browser = None
            return True
        except Exception as e:
            self.log.error(f"Failed to close browser: {e}")
            return False

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