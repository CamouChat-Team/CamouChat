"""WhatsApp chat processor for fetching and managing chats."""

from __future__ import annotations

import logging
import random
from typing import Dict, List, Optional

from playwright.async_api import Page, ElementHandle, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.Exceptions import ChatNotFoundError, ChatClickError, TweakioError
from src.Exceptions.whatsapp import ChatProcessorError, ChatUnreadError, ChatMenuError, ChatError
from src.Interfaces.chat_processor_interface import ChatProcessorInterface
from src.WhatsApp.DerivedTypes.Chat import whatsapp_chat
from src.WhatsApp.web_ui_config import WebSelectorConfig


class ChatProcessor(ChatProcessorInterface):
    """Fetches and manages WhatsApp chats from the Web UI."""

    def __init__(self, page: Page, log: logging.Logger, UIConfig: WebSelectorConfig):
        super().__init__(page=page, log=log, UIConfig=UIConfig)
        self.capabilities: Dict[str, bool] = {}
        if self.page is None:
            raise ValueError("page must not be None")

    async def fetch_chats(self, limit: int = 5, retry: int = 5) -> List[whatsapp_chat]:  # type: ignore[override]
        """Fetch visible chats from the sidebar."""
        ChatList: List[whatsapp_chat] = await self._get_Wrapped_Chat(limit=limit, retry=retry)

        if not ChatList:
            raise ChatNotFoundError("Chats Not Found on the Page.")

        return ChatList

    async def _get_Wrapped_Chat(self, limit: int, retry: int) -> List[whatsapp_chat]:  # type: ignore[override]
        """Extract chat elements and wrap them as `whatsapp_chat` objects."""
        sc = self.UIConfig
        wrapped: List[whatsapp_chat] = []
        try:
            chats = sc.chat_items()
            counter = 0
            while chats and not (await chats.count()) and counter < retry:
                chats = sc.chat_items()
                await self.page.wait_for_timeout(1000)
                counter += 1

            count = await chats.count() if chats else 0
            if not count or not chats:
                raise ChatNotFoundError("Chats Not Found.")

            minimum = min(count, limit)
            for i in range(minimum):
                wrapperChat = whatsapp_chat(
                    chat_ui=chats.nth(i), chat_name=await sc.getChatName(chats.nth(i))
                )
                wrapped.append(wrapperChat)

            return wrapped
        except TweakioError as e:
            raise ChatProcessorError("Failed to extract chat") from e

    async def _click_chat(self, chat: Optional[whatsapp_chat], **kwargs) -> bool:  # type: ignore[override]
        """Click on a chat to open it."""
        try:
            if not chat:
                raise ChatNotFoundError("none passed , expected chat in click chat")

            handle: Optional[ElementHandle] = (
                await chat.chat_ui.element_handle(timeout=1500)
                if isinstance(chat.chat_ui, Locator)
                else chat.chat_ui if chat.chat_ui is not None else None
            )

            if handle is None:
                raise ChatClickError(
                    "Chat Object is Given None in WhatsApp chat loader / _click_chat"
                )

            await handle.click(timeout=3500)
            return True
        except PlaywrightTimeoutError as e:
            raise ChatClickError("Failed to click chat in time.") from e
        except TweakioError as e:
            raise ChatClickError("Error in click the given chat.") from e

    @staticmethod
    async def is_unread(chat: Optional[whatsapp_chat]) -> int:
        """Check unread status. Returns 1 if unread with count, 0 otherwise."""
        try:
            if chat is None:
                raise ChatNotFoundError("none passed , expected chat in is_unread")

            handle: ElementHandle = (
                await chat.chat_ui.element_handle(timeout=1500)
                if isinstance(chat.chat_ui, Locator)
                else chat.chat_ui  # type: ignore[assignment]
            )

            unread_Badge = await handle.query_selector("[aria-label*='unread']")
            if unread_Badge:
                number_span = await unread_Badge.query_selector("span")
                if number_span:
                    text = (await number_span.inner_text()).strip()
                    if text.isdigit():
                        return 1
            return 0
        except TweakioError as e:
            raise ChatUnreadError("Error in is_unread checking") from e

    async def do_unread(self, chat: Optional[whatsapp_chat]) -> bool:
        """Mark a chat as unread via context menu."""
        page = self.page

        if chat is None:
            raise ChatNotFoundError("none passed , expected chat in do_unread")

        try:
            chat_handle: ElementHandle = (
                await chat.chat_ui.element_handle(timeout=1500)
                if isinstance(chat.chat_ui, Locator)
                else chat.chat_ui  # type: ignore[assignment]
            )

            if chat.chat_ui is None:
                raise ChatError("chat UI not initialized")

            await chat_handle.click(button="right")
            await page.wait_for_timeout(random.randint(1300, 2500))

            menu = await page.query_selector("role=application")
            if not menu:
                raise ChatMenuError("No chat menu found -- do_unread")

            unread_option = await menu.query_selector("li >> text=/mark.*as.*unread/i")

            if unread_option:
                await unread_option.click(timeout=random.randint(1701, 2001))
                self.log.info("whatsApp chat loader / [do_unread] Marked as unread ✅")
            else:
                read_option = await menu.query_selector("li >> text=/mark.*as.*read/i")
                if read_option:
                    self.log.info("whatsApp chat loader / [do_unread] Chat already unread")
                else:
                    self.log.info(
                        "whatsApp chat loader / [do_unread] Context menu option not found ❌"
                    )

            return True

        except PlaywrightTimeoutError as e:
            raise ChatUnreadError("Timeout while checking unread badge") from e

        except TweakioError as e:
            raise ChatUnreadError("Error in do_unread checking") from e
