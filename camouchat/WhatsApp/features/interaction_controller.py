"""WhatsApp reply functionality with message targeting."""

from __future__ import annotations

import asyncio
import os
import random
import tempfile
import weakref
from logging import Logger, LoggerAdapter
from typing import Union, Optional, Any

import pyperclip
from filelock import FileLock
from playwright.async_api import Page, ElementHandle, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from camouchat.Exceptions.base import ElementNotFoundError, HumanizedOperationError
from camouchat.Exceptions.whatsapp import ReplyCapableError
from camouchat.contracts.interaction_controller_interface import InteractionControllerInterface
from camouchat.WhatsApp.api import WapiSession
from camouchat.WhatsApp.api.models import MessageModelAPI
from camouchat.WhatsApp.core.web_ui_config import WebSelectorConfig
from camouchat.camouchat_logger import camouchatLogger

_clipboard_async_lock = asyncio.Lock()

_lock_file_path = os.path.join(tempfile.gettempdir(), "whatsapp_clipboard.lock")
_clipboard_file_lock = FileLock(_lock_file_path)


class ReplyCapable(InteractionControllerInterface):
    """Enables replying to specific WhatsApp messages."""

    _instances: weakref.WeakKeyDictionary[Page, ReplyCapable] = weakref.WeakKeyDictionary()
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> ReplyCapable:
        page = kwargs.get("page") or (args[0] if args else None)
        if page is None:
            return super(ReplyCapable, cls).__new__(cls)
        if page not in cls._instances:
            instance = super(ReplyCapable, cls).__new__(cls)
            cls._instances[page] = instance
        return cls._instances[page]

    def __init__(
        self,
        page: Page,
        ui_config: WebSelectorConfig,
        log: Optional[Union[LoggerAdapter, Logger]] = None,
        wapi: Optional[WapiSession] = None,
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.page = page
        self.ui_config = ui_config
        self.log = log or camouchatLogger
        if self.page is None:
            raise ValueError("page must not be None")
        self._wapi: Optional[WapiSession] = wapi
        self._initialized = True

    # ----------------------------------------------------
    # Humanize func
    async def send_api_text(
        self, text: str, chat_id: str, quoted_msg_id: Optional[str] = None
    ) -> bool:
        """
        Skips native OS usage & Directly send text via RAM Func.
        Initially supported for direct text msg sending only & works for Quoted Replies also.
        Don't support to send text with Media or other attachments.

        Gives Telemetry : mouse moves , msg box click & focus , for txt len > 50 chars , add ctrl C & ctrl V telemetry.
        Args :
            text : Text to be sent
            chat_id: Target chat ID
            quoted_msg_id: Optional message ID to quote/reply to
        Returns:
            bool: True if text is sent successfully.
        """

        if self._wapi is None:
            raise ValueError("WapiSession is not passed.")
        bridge = self._wapi.bridge
        try:
            inputBox = self.ui_config.message_box()
            await inputBox.click(timeout=5000)  # Telemetry
            self.log.debug("Msg Box Clicked.")

            if not chat_id:
                raise HumanizedOperationError("Could not determine active chat ID from bridge.")

            # typing state
            if await bridge.mark_is_composing(chat_id=chat_id):
                self.log.debug("Sent markIsComposing Successfully.")
            else:
                self.log.error("Failed to send MarkIsComposing.")

            if len(text) > 50:  # Telemetry
                await self.page.keyboard.press("Control+C")
                await asyncio.sleep(random.uniform(0.1, 0.4))
                await self.page.keyboard.press("Control+V")
                self.log.debug("Adding Ctrl C & Ctrl V Telemetry - DONE")

            sec = random.uniform(1.2, 2.5)
            self.log.debug(f"Sleeping for {sec} before API send to {chat_id}...")
            await asyncio.sleep(sec)

            options: dict[str, Any] = {"waitForAck": False}
            if quoted_msg_id:
                options["quotedMsg"] = quoted_msg_id

            self.log.debug("Invoking bridge.send_text_message...")
            success = await bridge.send_text_message(chat_id=chat_id, message=text, options=options)
            if success:
                self.log.debug("Text Sent via RAM Func.")
            else:
                self.log.error("Failed to send text via RAM Func.")
            return success

        except Exception as e:
            raise HumanizedOperationError(f"API Text typing failed: {e}") from e

    # ----------------------------------------------------

    async def reply(self, message: MessageModelAPI, text: Optional[str]) -> bool:
        """Reply to a message with optional text."""
        try:
            await self.quote(message)

            text = text or ""
            success = await self.type_text(
                text=text,
                send=True,
            )

            return success

        except PlaywrightTimeoutError as e:
            raise ReplyCapableError("reply timed out while preparing input box") from e

    async def quote(self, message: MessageModelAPI) -> bool:
        """Double-click the message container's side padding to trigger reply."""
        # ── Resolve data_id and direction ─────────────────────────────────────
        if not isinstance(message, MessageModelAPI):
            raise ReplyCapableError(
                f"Unsupported message type: {type(message)}. Expected MessageModelAPI."
            )

        if not message.id_serialized:
            raise ReplyCapableError("Message or data_id is missing.")

        data_id = str(message.id_serialized)
        from_me = self._message_from_me(message, data_id)
        retries = 10
        delay = 1.0

        for attempt in range(1, retries + 1):
            try:
                message_container = self._message_container_locator(data_id)
                clicked = await self._click_message_side_padding(
                    message_container,
                    data_id=data_id,
                    from_me=from_me,
                    click_count=2,
                )

                if clicked:
                    await self.page.wait_for_timeout(500)
                    return True

                self.log.debug(
                    f"[side_edge_click] Attempt {attempt}/{retries}: "
                    f"'{data_id}' has no usable bounding box."
                )

                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    raise ReplyCapableError(
                        f"side_edge_click failed after {retries} attempts: "
                        f"'{data_id}' never appeared in DOM."
                    )

            except ReplyCapableError:
                raise

            except Exception as e:
                self.log.error(f"[side_edge_click] Error on attempt {attempt}: {e}")
                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    raise ReplyCapableError(f"Unexpected error in side_edge_click: {e}") from e

        raise ReplyCapableError("side_edge_click failed after max attempts.")

    async def focus_input(
        self, source: ElementHandle | Locator | None = None
    ) -> ElementHandle | Locator:
        """Focus the WhatsApp message input or a provided input target."""
        target = source or self.ui_config.message_box()
        if not target:
            raise ElementNotFoundError("Input Element not found.")

        await target.click(timeout=5000)
        return target

    async def type_text(
        self,
        text: str,
        source: ElementHandle | Locator | None = None,
        send: bool = False,
    ) -> bool:
        """
        Type text with human-like delays.

        :param send: bool
        :param source:
        :param text: Text to type
        """

        target: ElementHandle | Locator | None = None
        try:
            target = await self.focus_input(source)
            await self.clear_input(target)
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

            if send:
                await self.enter()

            return True

        except (PlaywrightTimeoutError, PlaywrightError) as e:
            self.log.debug("Typing failed → fallback to instant fill", exc_info=e)
            return await self._Instant_fill(text=text, source=target or source, send=send)

    async def enter(self) -> None:
        """
        Presses Enter on the page, use it for confirm send after type.
        Given separately for Media based sending.
        For Media to be sent with text, you should follow first typing text, add_media now auto adds the text to the media's caption , now enter via page.
        :return:
        """
        await self.page.keyboard.press("Enter")

    async def clear_input(self, source: ElementHandle | Locator | None = None) -> None:
        """Clear the WhatsApp message input or a provided input target."""
        target = source or self.ui_config.message_box()
        if not target:
            raise ElementNotFoundError("Input Element not found.")

        await self._ensure_clean_input(target)

    @staticmethod
    def _css_attr_value(value: str) -> str:
        """Escape a string for use inside a double-quoted CSS attribute selector."""
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _message_container_locator(self, data_id: str) -> Locator:
        """Return the outer WhatsApp message wrapper by data-id only."""
        base_data_id = "_".join(data_id.split("_")[:3]) if data_id.count("_") >= 2 else data_id
        escaped_data_id = self._css_attr_value(data_id)
        escaped_base_data_id = self._css_attr_value(base_data_id)

        selector = f'div[data-id="{escaped_data_id}"]'
        if base_data_id != data_id:
            selector = f'{selector}, div[data-id^="{escaped_base_data_id}"]'

        return self.page.locator(selector).first

    async def _click_message_side_padding(
        self,
        message_container: Locator,
        *,
        data_id: str,
        from_me: bool,
        click_count: int = 1,
    ) -> bool:
        """Click the non-DOM side padding region of a message row."""
        await message_container.scroll_into_view_if_needed(timeout=3000)

        box = await message_container.bounding_box(timeout=3000)
        if not box or not box.get("width") or not box.get("height"):
            return False

        abs_x = box["x"] + box["width"] - 3 if from_me else box["x"] + 3
        abs_y = box["y"] + box["height"] / 2
        side = "right" if from_me else "left"

        self.log.debug(
            f"[message_side_padding_click] data-id='{data_id}', side={side} -> "
            f"CDP ({abs_x:.1f}, {abs_y:.1f}), click_count={click_count}"
        )
        await self.page.mouse.click(
            x=abs_x,
            y=abs_y,
            click_count=click_count,
            delay=random.randint(55, 70),
        )
        return True

    def _message_from_me(self, message: MessageModelAPI, data_id: str) -> bool:
        """Resolve message direction, falling back to WhatsApp's data-id prefix."""
        from_me = getattr(message, "fromMe", None)
        if from_me is not None:
            return bool(from_me)

        return data_id.startswith("true_")

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
        self,
        text: str,
        source: Optional[Union[ElementHandle, Locator]],
        send: bool = False,
    ) -> bool:
        """Fallback to instant fill when typing fails."""
        if not source:
            raise ElementNotFoundError("Source is Empty in _instant_fill.")

        try:
            await source.fill(text)
            if send:
                await self.enter()
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
            await loop.run_in_executor(None, _clipboard_file_lock.acquire)

            try:
                previous_clipboard = await loop.run_in_executor(None, pyperclip.paste)
                await loop.run_in_executor(None, pyperclip.copy, text)
                await asyncio.sleep(0.05)
                await self.page.keyboard.press("Control+V")
            finally:
                if previous_clipboard is not None:
                    await loop.run_in_executor(None, pyperclip.copy, previous_clipboard)
                await loop.run_in_executor(None, _clipboard_file_lock.release)
