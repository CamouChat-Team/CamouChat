"""WhatsApp Web login handler supporting QR and phone number authentication."""

from __future__ import annotations

import asyncio
import logging
import random
import re
import shutil
from pathlib import Path

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Locator
from typing import Optional
from src.Exceptions.whatsapp import LoginError
from src.Interfaces.login_interface import LoginInterface
from src.WhatsApp.web_ui_config import WebSelectorConfig


class Login(LoginInterface):
    """Handles WhatsApp Web authentication via QR code or phone number."""

    def __init__(self, page: Page, UIConfig: WebSelectorConfig, log: logging.Logger):
        if page is None:
            raise ValueError("page must not be None")

        super().__init__(page=page, UIConfig=UIConfig, log=log)
        self.UIConfig: WebSelectorConfig = UIConfig

    async def is_login_successful(self, **kwargs) -> bool:
        """Verify if login was successful by checking for chat list visibility."""
        timeout: int = kwargs.get("timeout", 10_000)
        chats = self.UIConfig.chat_list()
        try:
            await chats.wait_for(timeout=timeout, state="visible")
            return True
        except PlaywrightTimeoutError as e:
            raise TimeoutError("Timeout while checking for chat list.") from e

    async def login(self, **kwargs) -> bool:
        """
        Authenticate to WhatsApp Web.

        kwargs:
            method: 0 for QR, 1 for phone number (default: 1)
            wait_time: Timeout for QR scan in ms (default: 180_000)
            url: WhatsApp Web URL
            number: Phone number for code-based login
            country: Country name for phone login
        """
        method: int = kwargs.get("method", 1)
        wait_time: int = kwargs.get("wait_time", 180_000)
        link: str = kwargs.get("url", "https://web.whatsapp.com")
        number: Optional[int] = kwargs.get("number")
        country: Optional[str] = kwargs.get("country")

        try:
            await self.page.goto(link, timeout=60_000)
            await self.page.wait_for_load_state("networkidle", timeout=50_000)
        except PlaywrightTimeoutError as e:
            raise LoginError("Timeout while loading WhatsApp Web") from e

        if method == 0:
            success = await self.__qr_login(wait_time)
        elif method == 1:
            success = await self.__code_login(number, country)
        else:
            raise LoginError("Invalid login method. Use method=0 (QR) or method=1 (Code).")

        if success:
            self.log.info("WhatsApp login session stored successfully via persistent context.")

        return success

    async def __qr_login(self, wait_time: int) -> bool:
        """Wait for user to scan QR code."""
        canvas = self.UIConfig.qr_canvas()
        self.log.info("Waiting for QR scan (%s seconds)...", wait_time // 1000)

        try:
            await self.UIConfig.chat_list().wait_for(timeout=wait_time, state="visible")
            if await canvas.is_visible():
                raise LoginError("QR not scanned within allowed time.")
            return True
        except PlaywrightTimeoutError as e:
            raise LoginError("QR login timeout.") from e

    async def __code_login(self, number: int | None, country: str | None) -> bool:
        """Perform phone number based login with linking code."""
        if not number or not country:
            raise LoginError("Both number and country are required for code login.")

        self.log.info("Starting code-based login...")

        btn = self.page.get_by_role("button", name=re.compile("log.*in.*phone number", re.I))
        if await btn.count() == 0:
            raise LoginError("Login-with-phone-number button not found.")

        try:
            await btn.click(timeout=3000)
            await self.page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError as e:
            raise LoginError("Failed to open phone login screen.") from e

        ctl = self.page.locator("button:has(span[data-icon='chevron'])")
        if await ctl.count() == 0:
            raise LoginError("Country selector not found.")

        await ctl.click(timeout=3000)
        await self.page.keyboard.type(country, delay=random.randint(80, 120))
        await asyncio.sleep(1)

        countries: Locator = self.page.get_by_role("listitem").locator("button")
        if await countries.count() == 0:
            raise LoginError(f"No countries found for input: {country}")

        def normalize(name: str) -> str:
            return "".join(c for c in name if c.isalpha() or c.isspace()).lower().strip()

        target_country = normalize(country)
        selected = False

        for i in range(await countries.count()):
            el = countries.nth(i)
            name = normalize(await el.inner_text())
            if name == target_country:
                await el.click(timeout=3000)
                selected = True
                break

        if not selected:
            raise LoginError(f"Country '{country}' not selectable.")

        inp = self.page.locator("form >> input")
        if await inp.count() == 0:
            raise LoginError("Phone number input not found.")

        await inp.type(str(number), delay=random.randint(80, 120))
        await self.page.keyboard.press("Enter")

        code_el = self.page.locator("div[data-link-code]")
        try:
            await code_el.wait_for(timeout=10_000)
            code = await code_el.get_attribute("data-link-code")
            if not code:
                raise LoginError("Login code missing.")
            self.log.info("WhatsApp Login Code: %s", code)
        except PlaywrightTimeoutError as e:
            raise LoginError("Timeout while waiting for login code.") from e

        return True

    async def logout(self, state_dir: str, **kwargs) -> bool:  # type: ignore[override]
        """Clear session data from the specified directory."""
        try:
            path = Path(state_dir)

            if not path.exists() or not path.is_dir():
                self.log.warning(f"Logout skipped: invalid path {state_dir}")
                return False

            for item in path.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

            self.log.info(f"Logout cleanup successful for {state_dir}")
            return True

        except Exception as e:
            self.log.error(f"Logout cleanup failed: {e}", exc_info=True)
            return False
