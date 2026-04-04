"""
MessageApiManager — domain layer for WA-JS message operations.

Sits between WapiWrapper (raw stealth bridge) and the user-facing
decorator (msg_event_hook). This class:
  - Owns the message listener lifetime (start / stop).
  - Normalizes every raw dict coming from wajs_wrapper into MessageModelAPI.
  - Exposes direct RAM-pull methods (get_messages, get_message_by_id).

Type notation used in docstrings:
    RAM  = zero network cost, reads React in-memory stores.
    DISK = reads browser IndexedDB (local disk, slower than RAM).
"""

import asyncio
from logging import Logger, LoggerAdapter
from typing import Any, Callable, Dict, List, Optional, Union

from camouchat.camouchat_logger import camouchatLogger
from .wa_js.wajs_wrapper import WapiWrapper , WAJS_Scripts
from .models.message_api import MessageModelAPI


class MessageApiManager:
    """
    Domain manager for all WhatsApp message operations.

    Usage:
        bridge = WapiWrapper(page)
        await bridge.wait_for_ready()

        msg_api = MessageApiManager(bridge)

        # Event-driven — preferred (zero poll):
        await msg_api.start_listener(my_handler)

        # On-demand RAM pull:
        msgs = await msg_api.get_messages("91XXXX@c.us", count=10)
    """

    def __init__(
        self,
        bridge: WapiWrapper,
        log: Optional[Union[Logger, LoggerAdapter]] = None,
    ) -> None:
        self._bridge = bridge
        self.log = log or camouchatLogger
        self._bridge_active: bool = False
        self._handlers: List[Callable[[MessageModelAPI], Any]] = []

    # ──────────────────────────────────────────────
    # EVENT-DRIVEN LISTENER  (Push Architecture)
    # ──────────────────────────────────────────────

    def register_handler(self, callback: Callable[[MessageModelAPI], Any]) -> None:
        """
        Register a user callback to receive new messages.
        Called by @msg_event_hook — does NOT re-wire the DOM bridge.
        The bridge is set up once at WapiSession.start() via _setup_bridge().

        Args:
            callback: Async or sync function that receives a MessageModelAPI.
        """
        if callback not in self._handlers:
            self._handlers.append(callback)
            self.log.info(
                f"MessageApiManager: registered handler '{getattr(callback, '__name__', repr(callback))}' "
                f"(total={len(self._handlers)})"
            )

    async def _setup_bridge(self) -> None:
        """
        Wires the stealth DOM Bridge exactly ONCE at session start.
        Called by WapiSession.start() — NOT by the decorator.

        On every incoming WhatsApp message:
          1. Main World WPP hook fires → sends ONLY id_serialized across DOM.
          2. Isolated World catches the id → calls __get_new_message__.
          3. Raw dict fetched from React RAM, normalized → MessageModelAPI.
          4. All registered handlers are called with the clean object.
        """
        if self._bridge_active:
            self.log.warning("MessageApiManager: bridge already active, skipping re-setup.")
            return

        await self._bridge.setup_message_bridge(self.__get_new_message__)
        self._bridge_active = True
        self.log.info("MessageApiManager: DOM bridge active, ready to receive messages.")

    async def __get_new_message__(self, id_serialized: str) -> None:
        """
        Internal bridge callback — receives id_serialized from the Isolated World,
        fetches the full message from React RAM, normalizes it to MessageModelAPI,
        and fans it out to every registered handler.

        Args:
            id_serialized: The WPP message id e.g. 'true_916398@c.us_ABCDEF123'
        """
        try:
            raw: Dict[str, Any] = await self._bridge._evaluate_stealth(
                WAJS_Scripts.get_message_by_id(id_serialized)
            )
            if not raw:
                self.log.warning(
                    f"MessageApiManager: RAM lookup returned empty for id={id_serialized!r}"
                )
                return

            msg = MessageModelAPI.from_dict(raw)

            # Fan-out to all registered handlers
            for handler in list(self._handlers):
                try:
                    result = handler(msg)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:
                    self.log.error(
                        f"MessageApiManager: handler '{getattr(handler, '__name__', '?')}' "
                        f"raised on msg id={id_serialized!r}: {exc}"
                    )

        except Exception as exc:
            self.log.error(
                f"MessageApiManager: error processing message id={id_serialized!r}: {exc}"
            )

    async def stop_bridge(self) -> None:
        """
        Tears down the stealth DOM Bridge and clears all registered handlers.
        Called by WapiSession.stop().
        """
        await self._bridge.teardown_message_bridge()
        self._bridge_active = False
        self._handlers.clear()
        self.log.info("MessageApiManager: DOM bridge torn down, all handlers cleared.")


    # ──────────────────────────────────────────────
    # ON-DEMAND RAM PULL METHODS
    # ──────────────────────────────────────────────

    async def get_messages(
        self,
        chat_id: str,
        count: int = 50,
        direction: str = "before",
        only_unread: bool = False,
        media: Optional[str] = None,
        include_calls: bool = False,
        anchor_msg_id: Optional[str] = None,
    ) -> List[MessageModelAPI]:
        """
        Type: RAM — pulls messages from React MsgStore, zero network cost.

        Args:
            chat_id:        @c.us or @g.us JID.
            count:          Messages to fetch (-1 = all loaded in RAM).
            direction:      'before' (newest first, default) or 'after'.
            only_unread:    Only unread messages.
            media:          Filter: 'all' | 'image' | 'document' | 'url' | None.
            include_calls:  Include call log entries.
            anchor_msg_id:  id_serialized to paginate from.

        Returns:
            List[MessageModelAPI] — normalized, newest first.
        """
        raw_list: List[Dict[str, Any]] = await self._bridge._evaluate_stealth(
            WAJS_Scripts.get_messages(
                chat_id=chat_id,
                count=count,
                direction=direction,
                only_unread=only_unread,
                media=media,
                include_calls=include_calls,
                anchor_msg_id=anchor_msg_id,
            )
        )
        return [MessageModelAPI.from_dict(r) for r in (raw_list or [])]

    async def get_message_by_id(self, msg_id: str) -> Optional[MessageModelAPI]:
        """
        Type: RAM — fetch one message by its full serialized ID.

        Args:
            msg_id: e.g. 'true_916398014720@c.us_ABCDEF123'

        Returns:
            MessageModelAPI or None if not found in RAM.
        """
        raw: Optional[Dict[str, Any]] = await self._bridge._evaluate_stealth(
            WAJS_Scripts.get_message_by_id(msg_id)
        )
        if not raw:
            return None
        return MessageModelAPI.from_dict(raw)

    async def get_unread(self, chat_id: str) -> List[MessageModelAPI]:
        """
        Type: RAM — convenience shorthand for unread messages in a chat.
        """
        return await self.get_messages(chat_id, count=-1, only_unread=True)
