"""WhatsApp chat processor for fetching and managing chats."""

from __future__ import annotations

import asyncio
import random
import weakref
from logging import Logger, LoggerAdapter
from typing import Dict, List, Optional, Sequence, Union

from playwright.async_api import Page, ElementHandle, Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from camouchat.Exceptions import ChatNotFoundError, ChatClickError, CamouChatError
from camouchat.Exceptions.whatsapp import (
    ChatProcessorError,
    ChatUnreadError,
    ChatMenuError,
    ChatError,
)
from camouchat.Interfaces.chat_processor_interface import ChatProcessorInterface
from camouchat.WhatsApp.models.chat import Chat
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig


class ChatProcessor(ChatProcessorInterface):
    """Fetches and manages WhatsApp chats from the Web UI."""

    _instances: weakref.WeakKeyDictionary[Page, ChatProcessor] = weakref.WeakKeyDictionary()
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> ChatProcessor:
        page = kwargs.get("page") or (args[0] if args else None)
        if page is None:
            return super(ChatProcessor, cls).__new__(cls)
        if page not in cls._instances:
            instance = super(ChatProcessor, cls).__new__(cls)
            cls._instances[page] = instance
        return cls._instances[page]

    def __init__(
        self,
        page: Page,
        ui_config: WebSelectorConfig,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__(page=page, log=log, ui_config=ui_config)
        self.capabilities: Dict[str, bool] = {}
        if self.page is None:
            raise ValueError("page must not be None")
        self._initialized = True

    async def fetch_chats(
        self, limit: int = 5, retry: Optional[int] = 5, **kwargs
    ) -> Sequence[Chat]:
        """
        Fetch visible chats from the sidebar.

        :param limit: maximum number of chats to fetch
        :param retry: number of times to retry the request
        """
        ChatList: Sequence[Chat] = await self._get_Wrapped_Chat(limit=limit, retry=retry or 5)

        if not ChatList:
            raise ChatNotFoundError("Chats Not Found on the Page.")

        return ChatList

    async def _get_Wrapped_Chat(self, limit: int = 5, retry: int = 5, **kwargs) -> Sequence[Chat]:
        """Extract chat elements and wrap them."""

        sc = self.UIConfig

        for attempt in range(1, retry + 1):
            try:
                wrapped: List[Chat] = []

                chats = sc.chat_items()
                count = await chats.count() if chats else 0

                if not chats or count == 0:
                    raise ChatNotFoundError("Chats not found.")

                minimum = min(count, limit)

                for i in range(minimum):
                    chat_el = chats.nth(i)

                    name = await sc.getChatName(chat_el)

                    wrapped.append(
                        Chat(
                            chat_ui=chat_el,
                            chat_name=name,
                        )
                    )

                return wrapped

            except CamouChatError as e:
                if attempt < retry:
                    self.log.debug(f"[Retry {attempt}/{retry}] Chat fetch failed: {e}")
                    await asyncio.sleep(1)
                else:
                    self.log.error(f"Failed after {retry} retries (Chat fetch).")
                    raise ChatProcessorError(
                        f"Failed to extract chats after {retry} retries."
                    ) from e

            # unexpected bug → fail fast
            except Exception as e:
                self.log.error("Unexpected error in chat extraction", exc_info=True)
                raise ChatProcessorError("Unexpected failure in chat extraction.") from e

        raise ChatProcessorError("Unreachable state in chat extraction.")

    async def _click_chat(self, chat: Optional[Chat], **kwargs) -> bool:  # type: ignore[override]
        """Click on a chat purely using JS coordinates and CDP dispatch.

        Playwright's `locator.click()` can deadlock the entire python event loop
        trying to wait for OS mouse pointer stability. By bypassing it and
        sending a raw CDP mouse click, we are completely immune to interference.

        It will try repeatedly (up to 20 times, 1 second apart) to grab
        the element's bounding box and click it.
        """
        retries: int = kwargs.get("retries", 20)
        delay: float = kwargs.get("base_delay", 1.0)

        if not chat:
            raise ChatNotFoundError("None passed, expected Chat in _click_chat")

        chat_name = chat.chat_name

        for attempt in range(1, retries + 1):
            try:
                # Bypass actionability checks entirely by using JS to find exactly
                # where the chat is located currently.
                coords = await self.page.evaluate(
                    """(name) => {
                        const rows = document.querySelectorAll(
                            '[role="row"], [role="listitem"]'
                        );
                        for (const row of rows) {
                            const span = row.querySelector('span[title]');
                            if (span && span.title === name) {
                                const r = row.getBoundingClientRect();
                                return {
                                    x: r.left + r.width / 2,
                                    y: r.top + r.height / 2
                                };
                            }
                        }
                        return null;
                    }""",
                    chat_name,
                )

                if coords:
                    self.log.debug(
                        f"[_click_chat] Attempt {attempt}/{retries}: "
                        f"Injecting CDP click at {coords['x']}, {coords['y']} for '{chat_name}'."
                    )
                    await asyncio.sleep(random.uniform(0.2, 0.5))

                    await self.page.mouse.click(
                        coords["x"] + random.uniform(-2, 2),
                        coords["y"] + random.uniform(-2, 2),
                    )
                    return True

                # If no coords, DOM is probably re-rendering. Just fall through to retry.
                self.log.debug(
                    f"[_click_chat] Attempt {attempt}/{retries}: "
                    f"Chat '{chat_name}' not found in live DOM."
                )

                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    self.log.error(f"Failed to click '{chat_name}' after {retries} retries.")
                    raise ChatClickError(f"Exhausted retries clicking chat '{chat_name}'.")

            except CamouChatError:
                raise ChatClickError("CamouChat error in _click_chat.")

            except Exception as e:
                self.log.error(f"[_click_chat] Unexpected error on attempt {attempt}: {e}")
                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    raise ChatClickError("Unexpected failure in _click_chat.") from e

        raise ChatClickError("Unreachable state in _click_chat")

    @staticmethod
    async def is_unread(chat: Optional[Chat]) -> int:
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
        except CamouChatError as e:
            raise ChatUnreadError("Error in is_unread checking") from e

    async def do_unread(self, chat: Optional[Chat]) -> bool:
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

        except CamouChatError as e:
            raise ChatUnreadError("Error in do_unread checking") from e
