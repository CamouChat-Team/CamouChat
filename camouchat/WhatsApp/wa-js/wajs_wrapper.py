from logging import Logger, LoggerAdapter
from camouchat.camouchat_logger import camouchatLogger
from typing import Any, Callable, Dict, Optional, Union

from playwright.async_api import Page
from .wajs_scripts import WAJS_Scripts


class WAJSError(Exception):
    """Exception raised when wa-js execution fails structurally or within React."""

    pass


class WapiWrapper:
    """
    The Bridge connecting Playwright (Python execution space) to wa-js (Browser space).
    Parses and handles the stealth-wrapped JSON responses from WAJS_Scripts.
    """

    def __init__(self, page: Page, log: Optional[Union[LoggerAdapter, Logger]] = None):
        self.log = log or camouchatLogger()
        self.page = page

    async def _evaluate_stealth(self, js_string: str) -> Any:
        """
        Executes a Stealth JS script in the browser.
        Handles the extraction of our standard `{status: '...', data|message: '...'}` format.
        """
        # Prefix mw: to execute inside the website's context (bypassing Camoufox isolation)
        if not js_string.startswith("mw:"):
            js_string = "mw:" + js_string

        response = await self.page.evaluate(js_string)

        if not response or not isinstance(response, dict):
            raise WAJSError(f"Invalid stealth response format from browser: {response}")

        if response.get("status") == "error":
            # JS successfully swallowed a crash. We now raise it gracefully in Python.
            err_msg = response.get("message", "Unknown JavaScript Error in wa-js execution")
            self.log.error(f"WA-JS Execution Error: {err_msg}")
            raise WAJSError(err_msg)

        return response.get("data")

    # --- 1. SETUP & CORE ---
    async def wait_for_ready(self, timeout_ms: float = 30000) -> bool:
        """Wait until `wa-js` completes Webpack hijack and exposes WPP"""
        import asyncio
        import time

        self.log.info("Awaiting WPP.isReady flag via Main World polling...")

        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            try:
                # We use direct evaluation because wait_for_function fails in isolated contexts
                is_ready = await self.page.evaluate("mw:" + WAJS_Scripts.is_ready())
                if is_ready:
                    self.log.info("WPP successfully integrated and ready.")
                    return True
            except Exception:
                pass
            await asyncio.sleep(0.5)

        self.log.error("wa-js failed to initialize before timeout.")
        raise WAJSError("WPP Initialization Timeout")

    async def is_authenticated(self) -> bool:
        return await self._evaluate_stealth(WAJS_Scripts.is_authenticated())

    # --- 2. THE PUSH ARCHITECTURE (EVENTS) ---
    async def expose_message_listener(self, python_callback: Callable):
        """
        Exposes a Python handler to the browser to actively listen to WPP events.
        Zero-polling architecture.
        """
        alias = "__react_message_sync"

        # 1. Bind Python's callback to the browser's global JS space
        await self.page.expose_function(alias, python_callback)

        # 2. Tell WPP to start routing real-time WS payloads into our exposed function
        setup_script = WAJS_Scripts.setup_new_message_listener(alias)
        await self.page.evaluate("mw:" + setup_script)
        self.log.info(f"Stealth Message Push Listener activated via {alias}")

    # --- 3. DATA & ACTIONS ---
    async def get_chat(self, chat_id: str) -> Dict[str, Any]:
        return await self._evaluate_stealth(WAJS_Scripts.get_chat(chat_id))

    async def get_messages(self, chat_id: str, count: int = 50) -> list:
        return await self._evaluate_stealth(WAJS_Scripts.get_messages(chat_id, count))

    async def send_text_message(self, chat_id: str, message: str) -> Any:
        return await self._evaluate_stealth(WAJS_Scripts.send_text_message(chat_id, message))
