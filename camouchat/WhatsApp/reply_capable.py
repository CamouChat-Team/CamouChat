"""WhatsApp reply functionality with message targeting."""

from __future__ import annotations

import asyncio
import random
import weakref
from logging import Logger, LoggerAdapter
from typing import Optional, Union

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from camouchat.Exceptions.whatsapp import ReplyCapableError
from camouchat.Interfaces.reply_capable_interface import ReplyCapableInterface
from camouchat.WhatsApp.api.models import MessageModelAPI
from camouchat.WhatsApp.human_interaction_controller import HumanInteractionController
from camouchat.WhatsApp.models.message import Message
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig
from camouchat.WhatsApp.api import WapiSession


class ReplyCapable(
    ReplyCapableInterface[Message, HumanInteractionController, WebSelectorConfig]
):
    """Enables replying to specific WhatsApp messages."""

    _instances: weakref.WeakKeyDictionary[Page, ReplyCapable] = (
        weakref.WeakKeyDictionary()
    )
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
        super().__init__(page=page, log=log, ui_config=ui_config)
        if self.page is None:
            raise ValueError("page must not be None")
        self._wapi: Optional[WapiSession] = wapi
        self._initialized = True

    async def reply(
        self,
        message: Message | MessageModelAPI,
        humanize: HumanInteractionController,
        text: Optional[str],
        **kwargs,
    ) -> bool:
        """Reply to a message with optional text."""
        try:
            await self._side_edge_click(message)

            in_box = self.UIConfig.message_box()
            await in_box.click(timeout=3000)

            text = text or ""
            success = await humanize.typing(
                source=await in_box.element_handle(timeout=1000), text=text
            )

            if success:
                await self.page.keyboard.press("Enter")

            return success

        except PlaywrightTimeoutError as e:
            raise ReplyCapableError("reply timed out while preparing input box") from e

    async def _focus_message_in_dom(
        self,
        msg_id: str,
    ) -> bool:
        """
        Ask WPP to ensure the specific message is rendered in the live DOM.

        This handles two scenarios:
        1. If the message is already in the DOM, we do nothing.
        2. If the message is virtualized (scrolled away), we call WPP's
           scrollToMessage to force-render and mount the node.
        """
        if self._wapi is None:
            raise ValueError("wapi is None, give WapiSession instance first to use MessageModelAPI in reply.")

        try:
            exists = await self.page.evaluate(
                f"document.querySelector('div[data-id=\"{msg_id}\"]') !== null"
            )
            if exists:
                return True

            result = await self._wapi.bridge._evaluate_stealth(
                f"wpp.chat.scrollToMessage('{msg_id}')"
            )
            self.log.debug(f"[focus_message_in_dom] scrollToMessage result: {result!r}")
            return True
        except Exception as e:
            self.log.warning(f"[focus_message_in_dom] scrollToMessage failed: {e}")
            return False

    async def _side_edge_click(self, message: Message | MessageModelAPI) -> bool:
        """Double-click on message edge to trigger reply action.

        ─────────────────────────────────────────────────────────────────
        • `page.locator('[data-id="..."]').bounding_box()` internally calls
          `_with_element()` which snapshots an ElementHandle.  WhatsApp's
          virtual-scroll unmounts nodes during re-renders → "not attached to
          DOM" error.  The same applies to `.scroll_into_view_if_needed()`.

        • `page.evaluate(...)` (Isolated World) + `getBoundingClientRect()` +
          `scrollIntoView()` bypass the ElementHandle chain entirely and work
          against the live DOM.  Standard DOM APIs are fully accessible from
          Camoufox's Isolated World — no `mw:` prefix needed here.

        • Conclusion: keep the JS-based approach.  `page.locator` gives no
          advantage and reintroduces the stale-handle race for WA's
          virtual-scroll.

        ────────────────────────
        If a WapiWrapper was provided and the message is a MessageModelAPI,
        we call `_focus_message_in_dom` first to ensure WhatsApp's reconciler
        has rendered the bubble.  This is especially useful for messages that
        are above the current scroll position.
        """
        # ── Resolve data_id and direction ─────────────────────────────────────
        if isinstance(message, Message):
            if not message.data_id:
                raise ReplyCapableError("Message or data_id is missing.")
            data_id = str(message.data_id)
            is_incoming = getattr(message, "direction", "IN") == "IN"

        elif isinstance(message, MessageModelAPI):
            if not message.id_serialized:
                raise ReplyCapableError(
                    "MessageModelAPI.id_serialized is missing — cannot locate message in DOM."
                )
            data_id = message.id_serialized
            is_incoming = not bool(message.fromMe)

        else:
            raise ReplyCapableError(f"Unsupported message type: {type(message)}")

        if isinstance(message, MessageModelAPI) and self._wapi is not None:
            await self._focus_message_in_dom(data_id)
            await self.page.wait_for_timeout(300)

        retries = 20
        delay = 1.0

        for attempt in range(1, retries + 1):
            try:
                dims = await self.page.evaluate(
                    """(id) => {
                        const el = document.querySelector(`div[data-id="${id}"]`);
                        if (!el) return null;
                        el.scrollIntoView({ behavior: 'instant', block: 'center' });
                        const r = el.getBoundingClientRect();
                        return { x: r.left, y: r.top, width: r.width, height: r.height };
                    }""",
                    data_id,
                )

                if dims and dims.get("width") and dims.get("height"):
                    rel_x = dims["width"] * (0.2 if is_incoming else 0.8)
                    rel_y = dims["height"] / 2

                    abs_x = dims["x"] + rel_x
                    abs_y = dims["y"] + rel_y

                    self.log.debug(
                        f"[side_edge_click] Attempt {attempt}/{retries}: "
                        f"data-id='{data_id}' → CDP ({abs_x:.1f}, {abs_y:.1f})"
                    )
                    await self.page.mouse.click(
                        x=abs_x, y=abs_y, click_count=2, delay=random.randint(55, 70)
                    )
                    await self.page.wait_for_timeout(500)
                    return True

                else:
                    self.log.debug(
                        f"[side_edge_click] Attempt {attempt}/{retries}: "
                        f"'{data_id}' not found in DOM — node not yet rendered."
                    )

                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    raise ReplyCapableError(
                        f"side_edge_click: '{data_id}' never appeared in DOM after "
                        f"{retries} attempts."
                    )

            except ReplyCapableError:
                raise

            except Exception as e:
                self.log.error(f"[side_edge_click] Error on attempt {attempt}: {e}")
                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    raise ReplyCapableError(
                        f"Unexpected error in side_edge_click: {e}"
                    ) from e

        raise ReplyCapableError("side_edge_click failed after max attempts.")
