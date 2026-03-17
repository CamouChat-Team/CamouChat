"""WhatsApp reply functionality with message targeting."""

from __future__ import annotations

import logging
import random
from typing import Optional

from playwright.async_api import Page, Locator, Position
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from camouchat.WhatsApp.humanized_operations import HumanizedOperations
from camouchat.Exceptions.whatsapp import ReplyCapableError
from camouchat.Interfaces.reply_capable_interface import ReplyCapableInterface
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig
from camouchat.WhatsApp.models.message import Message


class ReplyCapable(ReplyCapableInterface):
    """Enables replying to specific WhatsApp messages."""

    UIConfig: WebSelectorConfig

    def __init__(self, page: Page, log: logging.Logger, UIConfig: WebSelectorConfig):
        super().__init__(page=page, log=log, UIConfig=UIConfig)
        if self.page is None:
            raise ValueError("page must not be None")

    async def reply(
        self,
        message: Message,  # type: ignore[override]
        humanize: HumanizedOperations,  # type: ignore[override]
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

    async def _side_edge_click(self, message: Message) -> bool:
        """Double-click on message edge to trigger reply action."""
        ui = message.message_ui
        try:
            if not ui:
                raise ReplyCapableError("Message UI is not accessible for reply edge click.")

            if isinstance(ui, Locator):
                ui = await ui.element_handle(timeout=1000)

            if not ui:
                raise ReplyCapableError("Message UI returned None on element_handle wait.")

            await ui.scroll_into_view_if_needed(timeout=2000)
            box = await ui.bounding_box()
            if not box:
                raise ReplyCapableError("message bounding box not available")

            rel_x = box["width"] * (0.2 if message.isIncoming() else 0.8)
            rel_y = box["height"] / 2

            await ui.click(
                position=Position(x=rel_x, y=rel_y),
                click_count=2,
                delay=random.randint(55, 70),
                timeout=3000,
            )

            await self.page.wait_for_timeout(timeout=500)
            return True

        except PlaywrightTimeoutError as e:
            raise ReplyCapableError("side_edge_click timed out while clicking message UI") from e
