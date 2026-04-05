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
import base64
from pathlib import Path
from logging import Logger, LoggerAdapter
from typing import Any, Callable, Dict, List, Optional, Union

from camouchat.camouchat_logger import camouchatLogger
from .models.message_api import MessageModelAPI
from .wa_js import WapiWrapper, WAJS_Scripts


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
        self._id_queue: asyncio.Queue = asyncio.Queue()
        self._drain_task: Optional[asyncio.Task] = None
        self._poll_task: Optional[asyncio.Task] = None

    # ──────────────────────────────────────────────
    # EVENT-DRIVEN LISTENER  (Push Architecture)
    # ──────────────────────────────────────────────

    def register_handler(self, callback: Callable[[MessageModelAPI], Any]) -> None:
        """
        Register a user callback to receive new messages.
        Called by @msg_event_hook .

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
        Wires the bridge exactly ONCE at session start.

        Flow per incoming message:
          1. Main World wpp.on fires → pushes id to window.__camou_queue__ (mw:).
          2. _poll_loop reads the queue every 100ms via mw: evaluate.
          3. Each id is put in _id_queue (asyncio.Queue).
          4. _drain_loop dequeues → RAM fetch → MessageModelAPI → handlers.
        """
        if self._bridge_active:
            self.log.warning("MessageApiManager: bridge already active, skipping re-setup.")
            return

        await self._bridge.setup_message_bridge()
        self._drain_task = asyncio.ensure_future(self._drain_loop())
        self._poll_task = asyncio.ensure_future(self._poll_loop())
        self._bridge_active = True
        self.log.info("MessageApiManager: DOM bridge active, ready to receive messages.")

    async def _poll_loop(self) -> None:
        """
        Polls window.__camou_queue__ in Main World every 100ms and feeds _id_queue.
        Runs via mw: evaluate — stays in Camoufox's real Main World context.
        """
        while True:
            try:
                ids = await self._bridge.poll_message_queue()
                for id_serialized in ids:
                    await self._id_queue.put(id_serialized)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.log.error(f"MessageApiManager: poll error: {exc}")
            await asyncio.sleep(0.1)


    async def _drain_loop(self) -> None:
        """
        Background task: drains the id queue and processes each message.
        Runs page.evaluate (RAM fetch) safely outside any expose_function callback.
        """
        while True:
            try:
                id_serialized = await self._id_queue.get()
                try:
                    await self.__get_new_message__(id_serialized)
                except Exception as exc:
                    self.log.error(f"MessageApiManager: drain loop error for id={id_serialized!r}: {exc}")
                finally:
                    self._id_queue.task_done()
            except asyncio.CancelledError:
                break

    async def __get_new_message__(self, id_serialized: str) -> None:
        """
        Fetches full message from React RAM by id, normalizes it,
        and fans it out to all registered handlers.
        Called from _drain_loop — NOT inside an expose_function callback.
        """
        try:
            raw: Dict[str, Any] = await self._bridge._evaluate_stealth(
                WAJS_Scripts.get_message_by_id(id_serialized)
            )
            if not raw:
                self.log.warning(
                    f"MessageApiManager: RAM lookup empty for id={id_serialized!r}"
                )
                return

            msg = MessageModelAPI.from_dict(raw)

            for handler in list(self._handlers):
                try:
                    result = handler(msg)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:
                    self.log.error(
                        f"MessageApiManager: handler '{getattr(handler, '__name__', '?')}' "
                        f"raised on id={id_serialized!r}: {exc}"
                    )
        except Exception as exc:
            self.log.error(
                f"MessageApiManager: error processing id={id_serialized!r}: {exc}"
            )

    async def stop_bridge(self) -> None:
        """
        Tears down the stealth DOM Bridge and clears all registered handlers.
        Called by WapiSession.stop().
        """
        for task in (self._poll_task, self._drain_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        await self._bridge.teardown_message_bridge()
        self._bridge_active = False
        self._handlers.clear()
        self.log.info("MessageApiManager: DOM bridge torn down, all handlers cleared.")

    # ──────────────────────────────────────────────
    # RAM BASED METHODS
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
        [Type: RAM]
        Pulls messages from React MsgStore with zero network cost.

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
        [Type: RAM]
        Fetch one message by its full serialized ID from React memory.

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
        [Type: RAM]
        Convenience shorthand for fetching only unread messages in a chat from memory.
        """
        return await self.get_messages(chat_id, count=-1, only_unread=True)

    async def decrypt_media(
        self,
        direct_path: str,
        media_key_b64: str,
        media_type: str,
        msg_id: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        [Type: RAM Primary / NETWORK Fallback]
        Extract and decrypt WhatsApp media. Tries to read from the browser Cache API
        (zero network) first. Falls back to wa-js's CDN downloader if the blob is missing.

        Args:
            direct_path:   msg['directPath']    — CDN path e.g. "/v/t62.7117-24/..."
            media_key_b64: msg['mediaKey']      — base64 AES root key (32 bytes)
            media_type:    msg['type']          — 'image'|'video'|'audio'|'ptt'|'document'|'sticker'
            msg_id:        msg['id_serialized'] — Required for CDN fallback only.
            save_path:     Optional filesystem path to write decrypted bytes to.

        Returns:
            Raw decrypted bytes, or None if both paths fail.
        """
        # Primary: Cache API (zero network)
        b64 = await self._bridge._evaluate_stealth(
            WAJS_Scripts.decrypt_media(
                direct_path=direct_path,
                media_key_b64=media_key_b64,
                media_type=media_type,
            )
        )

        if b64 is None:
            # Fallback: CDN download (NETWORK)
            if not msg_id:
                self.log.warning(
                    "decrypt_media: Cache miss & no msg_id passed. Cannot use CDN fallback."
                )
                return None

            self.log.info(f"decrypt_media: Cache miss for {direct_path!r} — CDN fallback [NETWORK]")
            b64 = await self._bridge._evaluate_stealth(WAJS_Scripts.download_media(msg_id=msg_id))

        if not b64:
            return None

        raw_bytes = base64.b64decode(b64)

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            Path(save_path).write_bytes(raw_bytes)
            self.log.info(f"decrypt_media: Saved {len(raw_bytes):,} bytes → {save_path}")

        return raw_bytes

    _MIME_TO_EXT: Dict[str, str] = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "video/mp4": ".mp4",
        "video/3gpp": ".3gp",
        "video/quicktime": ".mov",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/aac": ".aac",
        "application/pdf": ".pdf",
        "application/zip": ".zip",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }

    _TYPE_EXT_FALLBACK: Dict[str, str] = {
        "image": ".jpg",
        "video": ".mp4",
        "audio": ".ogg",
        "ptt": ".ogg",
        "sticker": ".webp",
        "document": ".bin",
    }

    @staticmethod
    def _ext_from_mime(mimetype: Optional[str], media_type: str = "image") -> str:
        """Derive file extension from mimetype, falling back to media_type."""
        if mimetype:
            base = mimetype.split(";")[0].strip().lower()
            if base in MessageApiManager._MIME_TO_EXT:
                return MessageApiManager._MIME_TO_EXT[base]
        return MessageApiManager._TYPE_EXT_FALLBACK.get(media_type, ".bin")

    @staticmethod
    def media_save_path(message: MessageModelAPI, save_dir: str) -> str:
        """Auto-generate a filesystem path for a media message."""
        ext = MessageApiManager._ext_from_mime(message.mimetype, message.MsgType or "media")
        safe_id = (
            (message.id_serialized or "unknown")
            .replace("/", "_")
            .replace("@", "_")
            .replace(":", "_")
        )
        return str(Path(save_dir) / f"{message.MsgType or 'media'}_{safe_id}{ext}")

    async def extract_media(
        self,
        message: MessageModelAPI,
        save_path: str,
    ) -> Dict[str, Any]:
        """
        [Type: RAM Primary / NETWORK Fallback]
        High-level media extraction directly from the normalized MessageModelAPI object.

        Args:
            message:   The populated MessageModelAPI.
            save_path: Full path where the decrypted file will be written.

        Returns:
            Dictionary with extraction success state, path, size, and metadata.
        """
        direct_path = message.directPath
        media_key_b64 = message.mediaKey
        media_type = message.MsgType or "image"
        msg_id = message.id_serialized

        result: Dict[str, Any] = {
            "success": False,
            "type": media_type,
            "mimetype": message.mimetype,
            "size_bytes": None,
            "path": None,
            "msg_id": msg_id,
            "view_once": message.isViewOnce,
            "used_fallback": False,
            "error": None,
        }

        if not direct_path:
            result["error"] = "Message has no directPath — not a downloadable media message."
            return result

        b64 = None
        if media_key_b64:
            b64 = await self._bridge._evaluate_stealth(
                WAJS_Scripts.decrypt_media(
                    direct_path=direct_path, media_key_b64=media_key_b64, media_type=media_type
                )
            )

        if b64 is None:
            if not msg_id:
                result["error"] = "Cache miss & no id_serialized — cannot use CDN fallback."
                return result
            self.log.info(f"extract_media: Cache miss for {direct_path!r} — CDN fallback [NETWORK]")
            result["used_fallback"] = True
            b64 = await self._bridge._evaluate_stealth(WAJS_Scripts.download_media(msg_id=msg_id))

        if not b64:
            result["error"] = "Both Cache api and CDN fallback returned None — media unavailable."
            return result

        raw_bytes = base64.b64decode(b64)
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        Path(save_path).write_bytes(raw_bytes)
        self.log.info(
            f"extract_media: [{media_type}] {len(raw_bytes):,} bytes → {save_path}"
            + (" [CDN fallback]" if result["used_fallback"] else " [Cache api]")
        )

        result.update({"success": True, "size_bytes": len(raw_bytes), "path": save_path})
        return result

    # ──────────────────────────────────────────────
    # INDEX DB BASED METHODS
    # ──────────────────────────────────────────────

    async def indexdb_get_messages(
        self,
        min_row_id: int,
        limit: int = 50,
    ) -> List[MessageModelAPI]:
        """
        [Type: INDEX DB]
        Fetch raw message data sequentially from IndexedDB storage across ALL chats directly from disk.
        Type: RAM (Disk). Messages are retrieved in order from min_row_id onwards.
        """
        raw_list = await self._bridge._evaluate_stealth(
            WAJS_Scripts.indexdb_get_messages(min_row_id=min_row_id, limit=limit)
        )
        return [MessageModelAPI.from_dict(r) for r in (raw_list or [])]

    # ──────────────────────────────────────────────
    # NETWORK BASED METHODS
    # ──────────────────────────────────────────────

    async def send_text_message(self, chat_id: str, message: str) -> Any:
        """
        [Type: NETWORK]
        Pure API text send. Sends the message entirely over the network.
        Use only when Playwright UI interaction logic is bypassing the actual input field.
        """
        return await self._bridge._evaluate_stealth(
            WAJS_Scripts.send_text_message(chat_id, message)
        )
