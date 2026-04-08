from playwright.async_api import Page
from logging import Logger, LoggerAdapter
from typing import Any
import random
import asyncio
from camouchat.camouchat_logger import camouchatLogger
from .models import ChatModelAPI
from .wa_js import WapiWrapper, WAJS_Scripts


class ChatApiManager:
    def __init__(self, bridge: WapiWrapper, logger: Logger | LoggerAdapter | None = None) -> None:
        self._bridge = bridge
        self.log = logger or camouchatLogger
        self._last_opened_chat_id: str | None = None

    async def open_chat(self, chat: ChatModelAPI, page: Page) -> bool:
        """
        Opens the chat using a Stealth Hybrid approach.
        1. Tries to find the chat physically on the screen and injects human CDP mouse clicks.
        2. If virtualized (hidden), falls back to the RAM bridge.
        """

        if chat is None:
            raise ValueError("Chat is None, cannot open chat")

        if chat.id_serialized == self._last_opened_chat_id:
            self.log.debug(f"Chat {chat.id_serialized} is already the active view based on cache.")
            return True

        
        # If we don't have a formatted Title, we cannot safely scrape the DOM. Skip to RAM fallback.
        if chat.formattedTitle:
            self.log.debug(f"Locating chat: {chat.formattedTitle} ({chat.id_serialized})")
            
            try:
                chat_locator = (
                    page.locator("div#pane-side, div[aria-label*='Chat list' i]")
                    .locator(f"span[title='{chat.formattedTitle}']")
                    .first
                )

                if await chat_locator.count() > 0 and await chat_locator.is_visible(timeout=5000):
                    box = await chat_locator.bounding_box()
                    if box:
                        # Calculate center coordinates
                        target_x = box["x"] + (box["width"] / 2)
                        target_y = box["y"] + (box["height"] / 2)

                        self.log.debug(
                            f"Chat physically visible. Injecting physical CDP click at {target_x}, {target_y}."
                        )

                        # Humanize Movement
                        await page.mouse.move(
                            target_x + random.uniform(-10, 10), target_y + random.uniform(-10, 10)
                        )
                        await asyncio.sleep(random.uniform(0.1, 0.4))

                        # Hardware level click, bypasses execution locks
                        await page.mouse.click(
                            target_x + random.uniform(-2, 2),
                            target_y + random.uniform(-2, 2),
                        )
                        self._last_opened_chat_id = chat.id_serialized
                        return True
            except Exception as e:
                self.log.warning(f"Stealth DOM scrape failed for {chat.formattedTitle}, reverting to RAM: {e}")

        # Virtualized DOM Fallback
        self.log.debug(f"Chat '{chat.formattedTitle or chat.id_serialized}' not visible on screen. Triggering RAM open.")

        # Inject ambient human pointer telemetry before triggering magical DOM re-renders.
        await page.mouse.move(random.randint(150, 800), random.randint(150, 600))
        await asyncio.sleep(random.uniform(1.8, 2.5))

        try:
            await self._bridge._evaluate_stealth(
                f'window.WPP.chat.openChatBottom("{chat.id_serialized}")'
            )
            self._last_opened_chat_id = chat.id_serialized
            return True

        except Exception as e:
            self.log.error(f"Failed to open chat {chat.id_serialized}: {e}")
            return False

    # ──────────────────────────────────────────────
    # RAM BASED METHODS
    # ──────────────────────────────────────────────

    async def get_chat_by_id(self, chat_id: str) -> ChatModelAPI:
        """
        [Type: RAM]
        Fetch all the scalar data from React memory structured via ChatModelAPI.

        Args:
            chat_id: The @c.us or @g.us ID.
        Returns:
            ChatModelAPI containing the chat metadata.
        """
        raw_data = await self._bridge._evaluate_stealth(WAJS_Scripts.get_chat(chat_id))
        return ChatModelAPI.from_dict(raw_data)

    async def get_chat_list(
        self,
        count: int | None = None,
        direction: str = "after",
        only_users: bool = False,
        only_groups: bool = False,
        only_communities: bool = False,
        only_unread: bool = False,
        only_archived: bool = False,
        only_newsletter: bool = False,
        with_labels: list | None = None,
        anchor_chat_id: str | None = None,
        ignore_group_metadata: bool = True,
    ) -> list[ChatModelAPI]:
        """
        [Type: RAM]
        Fetch a list of chats from ChatStore in sidebar order directly from React memory.

        Args:
            count:                  Max chats. None = all.
            direction:              'after' (default) or 'before' anchor_chat_id.
            only_users:             Only 1-on-1 personal chats.
            only_groups:            Only group chats.
            only_communities:       Only Community parent groups.
            only_unread:            Only chats with unread messages.
            only_archived:          Only archived chats.
            only_newsletter:        Only WhatsApp Channels.
            with_labels:            Filter by label name/ID (Business accounts).
            anchor_chat_id:         Chat ID to paginate from.
            ignore_group_metadata:  Skip group member fetching (faster, True by default).

        Returns:
            List of structured ChatModelAPI objects, same order as WhatsApp sidebar.
        """
        raw_list = await self._bridge._evaluate_stealth(
            WAJS_Scripts.list_chats(
                count=count,
                direction=direction,
                only_users=only_users,
                only_groups=only_groups,
                only_communities=only_communities,
                only_unread=only_unread,
                only_archived=only_archived,
                only_newsletter=only_newsletter,
                with_labels=with_labels,
                anchor_chat_id=anchor_chat_id,
                ignore_group_metadata=ignore_group_metadata,
            )
        )
        return [ChatModelAPI.from_dict(c) for c in (raw_list or [])]

    # ──────────────────────────────────────────────
    # NETWORK BASED METHODS
    # ──────────────────────────────────────────────

    async def mark_is_read(self, chat_id: str) -> Any:
        """
        [Type: NETWORK]
        Force-mark a chat as read. Sends a network read-receipt to WhatsApp servers.
        Only call when using Tier 3 pure API mode.

        Args:
            chat_id: The chat to mark as read.
        """
        return await self._bridge._evaluate_stealth(WAJS_Scripts.mark_is_read(chat_id))
