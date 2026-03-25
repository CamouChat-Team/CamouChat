import asyncio
import base64
import time
import uuid
import codecs
import os
from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from playwright.async_api import Page

from camouchat.camouchat_logger import camouchatLogger
from .wajs_scripts import WAJS_Scripts
from camouchat.Exceptions.whatsapp import WAJSError


class WapiWrapper:
    """
    The Bridge connecting Playwright (Python) to wa-js (Browser).

    Architecture:
        - Reads data via a CustomEvent bridge (Isolated World → Main World → Isolated World).
        - All WPP calls route through the hidden `window.__react_devtools_hook` reference
          (WPP is deleted from window after injection to avoid Meta's integrity scanners).
        - Errors are swallowed in JS, formatted, and re-raised cleanly as WAJSError in Python.
    """

    def __init__(self, page: Page, log: Optional[Union[LoggerAdapter, Logger]] = None):
        self.page = page
        self.log = log or camouchatLogger

    async def _evaluate_stealth(self, js_fragment: str) -> Any:
        """
        Executes a JS expression inside the Main World via a CustomEvent bridge.

        Flow:
            1. Isolated World sets up a one-shot listener for a unique CustomEvent.
            2. A <script> tag is injected into the DOM (runs in Main World).
            3. Main World evaluates `js_fragment` with access to `window.__react_devtools_hook`.
            4. Result or error is dispatched back as a CustomEvent detail.
            5. Isolated World receives it and resolves the Promise back to Python.

        Args:
            js_fragment: A raw JS expression/IIFE that may be async.
                         Has access to `const wpp = window.__react_devtools_hook;`

        Returns:
            Deserialized Python object from the JSON result.

        Raises:
            WAJSError: If JS throws or the bridge returns an error status.
        """
        req_id = f"camou_{uuid.uuid4().hex}"

        bridge_script = f"""() => {{
            return new Promise((resolve) => {{
                // 1. Isolated World: listen for result dispatched from the Main World
                window.addEventListener('{req_id}', (e) => {{
                    resolve(e.detail);
                }}, {{ once: true }});

                // 2. Build and inject a <script> tag into the real DOM (executes in Main World)
                const script = document.createElement('script');
                const nonceEl = document.querySelector('script[nonce]');
                if (nonceEl) script.setAttribute('nonce', nonceEl.nonce);

                script.textContent = `
                    (async () => {{
                        try {{
                            const wpp = window.__react_devtools_hook;
                            if (!wpp) throw new Error("Hidden WPP handle missing. Was wait_for_ready() called?");

                            const res = await ({js_fragment});
                            window.dispatchEvent(new CustomEvent('{req_id}', {{
                                detail: {{ status: 'success', data: res }}
                            }}));
                        }} catch (err) {{
                            window.dispatchEvent(new CustomEvent('{req_id}', {{
                                detail: {{ status: 'error', message: err.toString() }}
                            }}));
                        }}
                    }})();
                `;
                document.documentElement.appendChild(script);
                script.remove();
            }});
        }}"""

        response = await self.page.evaluate(bridge_script)

        if not response or not isinstance(response, dict):
            raise WAJSError(f"Invalid stealth bridge response: {response}")

        if response.get("status") == "error":
            err_msg = response.get("message", "Unknown JS error in wa-js execution")
            self.log.error(f"WA-JS Error: {err_msg}")
            raise WAJSError(err_msg)

        return response.get("data")

    # ─────────────────────────────────────────────
    # 1. SETUP & LIFECYCLE
    # ─────────────────────────────────────────────

    async def wait_for_ready(self, timeout_ms: float = 60000) -> bool:
        """
        Injects wppconnect-wa.js into the Main World, waits for WPP to init,
        then performs the 'Smash & Grab' — hides WPP under a non-enumerable
        property (`window.__react_devtools_hook`) and deletes `window.WPP`
        to evade Meta's integrity.js scanners.
        """
        js_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "wppconnect-wa.js"))
        with codecs.open(js_path, "r", "utf-8") as f:
            js_code = f.read()

        self.log.info("Injecting WPP engine and waiting for Webpack integration...")

        start = time.time()
        injected = False

        while (time.time() - start) * 1000 < timeout_ms:
            try:
                if not injected:
                    has_global = await self.page.evaluate("mw:typeof window.WPP !== 'undefined'")
                    if not has_global:
                        try:
                            await self.page.evaluate(
                                """([jsCode]) => {
                                    const script = document.createElement('script');
                                    const nonceEl = document.querySelector('script[nonce]');
                                    if (nonceEl) script.setAttribute('nonce', nonceEl.nonce);
                                    script.textContent = jsCode;
                                    document.documentElement.appendChild(script);
                                    script.remove();
                                }""",
                                [js_code],
                            )
                            injected = True
                        except Exception as e:
                            if "Execution context was destroyed" not in str(e):
                                self.log.warning(f"DOM injection failed: {e}")
                    else:
                        injected = True

                if injected:
                    is_ready = await self.page.evaluate(
                        "mw:window.WPP && window.WPP.isReady === true"
                    )
                    if is_ready:
                        # Smash & Grab: hide WPP under a non-enumerable cache key
                        await self.page.evaluate("""mw:(() => {
                            Object.defineProperty(window, "__react_devtools_hook", {
                                value: window.WPP,
                                enumerable: false,
                                configurable: true,
                                writable: true
                            });
                            delete window.WPP;
                        })()""")
                        self.log.info(
                            "WPP engine integrated! Global 'window.WPP' successfully "
                            "completely annihilated and converted to stealth property."
                        )
                        return True

            except Exception as e:
                if "Execution context was destroyed" in str(e):
                    injected = False
                else:
                    self.log.warning(f"Error evaluating WPP status: {e}")

            await asyncio.sleep(0.5)

        self.log.error("wa-js failed to initialize before timeout.")
        raise WAJSError(f"WPP Initialization Timeout (waited {timeout_ms / 1000:.0f}s)")

    async def is_authenticated(self) -> bool:
        """Check if WhatsApp session is currently authenticated."""
        return await self._evaluate_stealth(WAJS_Scripts.is_authenticated())

    # ─────────────────────────────────────────────
    # 2. PUSH ARCHITECTURE — EVENT LISTENER
    # ─────────────────────────────────────────────

    async def expose_message_listener(self, python_callback: Callable) -> None:
        """
        Zero-poll message pipeline: Exposes a Python handler to the browser,
        then instructs WPP to push every incoming message directly into it.

        Args:
            python_callback: Python async/sync function receiving a dict with message fields.
        """
        alias = "__react_message_sync"
        await self.page.expose_function(alias, python_callback)

        setup_script = WAJS_Scripts.setup_new_message_listener(alias)
        await self.page.evaluate("mw:" + setup_script)
        self.log.info(f"Stealth Message Push Listener activated via {alias}")

    # ─────────────────────────────────────────────
    # 3. DATA FETCHING
    # ─────────────────────────────────────────────

    async def get_chat_list(
        self,
        count: Optional[int] = None,
        direction: str = "after",
        only_users: bool = False,
        only_groups: bool = False,
        only_communities: bool = False,
        only_unread: bool = False,
        only_archived: bool = False,
        only_newsletter: bool = False,
        with_labels: Optional[List] = None,
        anchor_chat_id: Optional[str] = None,
        ignore_group_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch a list of chats from ChatStore in sidebar order.

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
            List of raw ChatModel dicts, same order as WhatsApp sidebar.
        """
        return await self._evaluate_stealth(
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

    async def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Fetch all scalar metadata for a chat from React memory."""
        return await self._evaluate_stealth(WAJS_Scripts.get_chat(chat_id))

    async def get_messages(
        self,
        chat_id: str,
        count: int = 50,
        direction: str = "before",
        only_unread: bool = False,
        media: Optional[str] = None,
        include_calls: bool = False,
        anchor_msg_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch messages for a chat from React RAM.

        Args:
            chat_id:        The @c.us or @g.us ID.
            count:          Number of messages (-1 for all).
            direction:      'before' (default) or 'after' anchor_msg_id.
            only_unread:    Only return messages user hasn't seen.
            media:          Filter to 'all' | 'image' | 'document' | 'url' | None.
            include_calls:  Include call_log entries in results.
            anchor_msg_id:  Full message ID to paginate from.

        Returns:
            List of message dicts with id, body, type, from, to, timestamp, etc.
        """
        return await self._evaluate_stealth(
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

    async def get_message_by_id(self, msg_id: str) -> Dict[str, Any]:
        """
        Fetch one specific message by its full serialized ID.

        Args:
            msg_id: Full message key e.g. 'true_916398014720@c.us_ABCDE123'
        """
        return await self._evaluate_stealth(WAJS_Scripts.get_message_by_id(msg_id))

    # ─────────────────────────────────────────────
    # 4. ACTIONS — TIER 3 FALLBACKS
    # ─────────────────────────────────────────────

    async def send_text_message(self, chat_id: str, message: str) -> Any:
        """
        Pure API text send (Tier 3 fallback).
        Use only when Playwright UI interaction fails.
        """
        return await self._evaluate_stealth(WAJS_Scripts.send_text_message(chat_id, message))

    async def mark_is_read(self, chat_id: str) -> Any:
        """Force-mark a chat as read. Only call when using Tier 3 pure API mode."""
        return await self._evaluate_stealth(WAJS_Scripts.mark_is_read(chat_id))

    # ─────────────────────────────────────────────
    # 5. INDEXDB — DISK HISTORY
    # ─────────────────────────────────────────────

    async def indexdb_get_messages(
        self,
        min_row_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw message data sequentially from IndexedDB storage across ALL chats.
        Type: RAM (Disk)
        Note: Messages are retrieved in order from min_row_id onwards.
        """
        return await self._evaluate_stealth(
            WAJS_Scripts.indexdb_get_messages(min_row_id=min_row_id, limit=limit)
        )

    # ─────────────────────────────────────────────
    # 5b. MEDIA DECRYPTION
    # ─────────────────────────────────────────────

    async def decrypt_media(
        self,
        direct_path: str,
        media_key_b64: str,
        media_type: str,
        msg_id: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Extract and decrypt WhatsApp media using the fields embedded in the raw MsgModel dump.
        Primary path reads directly from the browser Cache API — zero network cost.
        Falls back to wa-js's CDN downloader if the blob is not yet cached.

        Type: RAM (Cache API primary) / NETWORK (CDN fallback — logs INFO when triggered)

        Args:
            direct_path:   msg['directPath']    — CDN path e.g. "/v/t62.7117-24/..."
            media_key_b64: msg['mediaKey']      — base64 AES root key (32 bytes)
            media_type:    msg['type']          — 'image'|'video'|'audio'|'ptt'|'document'|'sticker'
            msg_id:        msg['id_serialized'] — Required for CDN fallback only.
            save_path:     Optional filesystem path to write decrypted bytes to.

        Returns:
            Raw decrypted bytes, or None if both paths fail.

        Raw MsgModel fields needed:
            directPath, mediaKey, type  (+id_serialized for fallback)
        """
        # ── Primary: Cache API (zero network) ───────────────────────────────
        b64 = await self._evaluate_stealth(
            WAJS_Scripts.decrypt_media(
                direct_path=direct_path,
                media_key_b64=media_key_b64,
                media_type=media_type,
            )
        )

        if b64 is None:
            # ── Fallback: wa-js CDN download (NETWORK) ───────────────────────
            if not msg_id:
                self.log.warning(
                    "decrypt_media: Cache miss and no msg_id provided — cannot use CDN fallback."
                )
                return None

            self.log.info(
                f"decrypt_media: Cache miss for {direct_path!r} — "
                f"falling back to CDN download via wpp.chat.downloadMedia() [NETWORK]"
            )
            b64 = await self._evaluate_stealth(WAJS_Scripts.download_media(msg_id=msg_id))

        if not b64:
            return None

        raw_bytes = base64.b64decode(b64)

        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            Path(save_path).write_bytes(raw_bytes)
            self.log.info(f"decrypt_media: Saved {len(raw_bytes):,} bytes → {save_path}")

        return raw_bytes

    # MIME type → file extension map for auto-naming saved media
    _MIME_TO_EXT: Dict[str, str] = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/avif": ".avif",
        "video/mp4": ".mp4",
        "video/3gpp": ".3gp",
        "video/quicktime": ".mov",
        "audio/ogg": ".ogg",
        "audio/mp4": ".m4a",
        "audio/mpeg": ".mp3",
        "audio/aac": ".aac",
        "audio/amr": ".amr",
        "application/pdf": ".pdf",
        "application/zip": ".zip",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
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
            if base in WapiWrapper._MIME_TO_EXT:
                return WapiWrapper._MIME_TO_EXT[base]
        return WapiWrapper._TYPE_EXT_FALLBACK.get(media_type, ".bin")

    @staticmethod
    def media_save_path(message: Dict[str, Any], save_dir: str) -> str:
        """
        Auto-generate a filesystem path for a media message.

        Args:
            message:  Raw MsgModel dict from get_messages() / get_message_by_id()
            save_dir: Directory where the file should be saved (created if absent)

        Returns:
            Full absolute path string, e.g. /path/to/dir/image_false_91XX_ABCD.jpg
        """
        msg_id = message.get("id_serialized", "unknown")
        media_type = message.get("type", "media")
        mimetype = message.get("mimetype") or message.get("mime_type")
        ext = WapiWrapper._ext_from_mime(mimetype, media_type)
        safe_id = msg_id.replace("/", "_").replace("@", "_").replace(":", "_")
        return str(Path(save_dir) / f"{media_type}_{safe_id}{ext}")

    async def extract_media(
        self,
        message: Dict[str, Any],
        save_path: str,
    ) -> Dict[str, Any]:
        """
        High-level media extraction from a raw MsgModel dump.

        Reads directPath + mediaKey + type directly from the message dict,
        tries the Cache API first (zero network), falls back to CDN if needed,
        writes the file to save_path, and returns a structured result dict.

        Type: RAM (Cache API primary) / NETWORK (CDN fallback — logged as INFO)

        Args:
            message:   Raw MsgModel dict from get_messages() or get_message_by_id().
                       Required fields: directPath, type
                       Optional fields: mediaKey (needed for Cache API decrypt),
                                        id_serialized (needed for CDN fallback)
            save_path: Full path where the decrypted file will be written.
                       Use media_save_path(message, save_dir) to auto-generate.

        Returns:
            {
                "success":       bool,        # True if bytes were saved
                "type":          str,          # "image"|"video"|"audio"|"ptt"|"document"|"sticker"
                "mimetype":      str | None,   # e.g. "image/jpeg"
                "size_bytes":    int | None,   # file size on success
                "path":          str | None,   # absolute path to saved file
                "msg_id":        str | None,   # id_serialized from the message
                "view_once":     bool,         # True if this was a view-once message
                "used_fallback": bool,         # True if CDN download [NETWORK] was used
                "error":         str | None,   # human-readable error on failure
            }

        Raw MsgModel fields consumed:
            directPath, mediaKey, type, id_serialized, mimetype, viewOnce / isViewOnce
        """
        direct_path = message.get("directPath")
        media_key_b64 = message.get("mediaKey")
        media_type = message.get("type", "image")
        msg_id = message.get("id_serialized")
        mimetype = message.get("mimetype") or message.get("mime_type")
        view_once = bool(message.get("viewOnce") or message.get("isViewOnce"))

        result: Dict[str, Any] = {
            "success": False,
            "type": media_type,
            "mimetype": mimetype,
            "size_bytes": None,
            "path": None,
            "msg_id": msg_id,
            "view_once": view_once,
            "used_fallback": False,
            "error": None,
        }

        if not direct_path:
            result["error"] = "Message has no directPath — not a downloadable media message."
            return result

        # ── Primary: Cache API (zero network) ──────────────────────────────────
        b64 = await self._evaluate_stealth(
            WAJS_Scripts.decrypt_media(
                direct_path=direct_path,
                media_key_b64=media_key_b64,
                media_type=media_type,
            )
        )

        if b64 is None:
            # ── Fallback: CDN download (NETWORK) ───────────────────────────────
            if not msg_id:
                result["error"] = (
                    "Cache miss and no id_serialized in message — cannot use CDN fallback."
                )
                return result

            self.log.info(
                f"extract_media: Cache miss for {direct_path!r} — "
                f"falling back to CDN download via wpp.chat.downloadMedia() [NETWORK]"
            )
            result["used_fallback"] = True
            b64 = await self._evaluate_stealth(WAJS_Scripts.download_media(msg_id=msg_id))

        if not b64:
            result["error"] = "Both Cache API and CDN fallback returned None — media unavailable."
            return result

        raw_bytes = base64.b64decode(b64)

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        Path(save_path).write_bytes(raw_bytes)
        self.log.info(
            f"extract_media: [{media_type}] {len(raw_bytes):,} bytes → {save_path}"
            + (" [CDN fallback]" if result["used_fallback"] else " [Cache API]")
        )

        result.update(
            {
                "success": True,
                "size_bytes": len(raw_bytes),
                "path": save_path,
            }
        )
        return result

    # ─────────────────────────────────────────────
    # 6. NEWSLETTER (CHANNELS)
    # ─────────────────────────────────────────────

    async def newsletter_list(self) -> List[Dict[str, Any]]:
        """
        Fetch all WhatsApp Channels (Newsletters) you follow.
        Returns raw ChatModel dicts (same shape as get_chat_list()).
        """
        return await self._evaluate_stealth(WAJS_Scripts.newsletter_list())

    async def newsletter_search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search the WhatsApp Channel directory.

        Args:
            query: Search term (e.g. 'technology', 'news').
            limit: Max results to return (default 20).

        Returns:
            Raw dict with 'newsletters' list and optional 'pageInfo' for pagination.
        """
        return await self._evaluate_stealth(
            WAJS_Scripts.newsletter_search(query=query, limit=limit)
        )

    async def newsletter_follow(self, newsletter_id: str) -> bool:
        """
        Follow / subscribe to a WhatsApp Channel.

        Args:
            newsletter_id: The @newsletter JID e.g. '120363xxxxx@newsletter'.
        """
        return await self._evaluate_stealth(WAJS_Scripts.newsletter_follow(newsletter_id))

    async def newsletter_unfollow(self, newsletter_id: str) -> bool:
        """
        Unfollow / unsubscribe from a WhatsApp Channel.

        Args:
            newsletter_id: The @newsletter JID e.g. '120363xxxxx@newsletter'.
        """
        return await self._evaluate_stealth(WAJS_Scripts.newsletter_unfollow(newsletter_id))

    async def newsletter_mute(self, newsletter_id: str) -> Any:
        """Mute notifications for a WhatsApp Channel."""
        return await self._evaluate_stealth(WAJS_Scripts.newsletter_mute(newsletter_id))

    async def newsletter_unmute(self, newsletter_id: str) -> Any:
        """Unmute notifications for a WhatsApp Channel."""
        return await self._evaluate_stealth(WAJS_Scripts.newsletter_unmute(newsletter_id))

    # ═══════════════════════════════════════════════════════════
    # READ-LEVEL — DATA & INTROSPECTION
    # ═══════════════════════════════════════════════════════════

    # ─────────────────────────────────────────────
    # 7. CONN — Session & Device Info (READ)
    # ─────────────────────────────────────────────

    async def conn_get_my_user_id(self) -> Any:
        """
        Type: RAM (AccountStore — zero network cost, call freely).
        Returns: str — your own WhatsApp ID e.g. '919876543210@c.us'
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_my_user_id())

    async def conn_get_my_user_lid(self) -> Any:
        """
        Type: RAM (AccountStore).
        Returns: str — hardware-bound Linked Device ID e.g. '37358229573849@lid'.
                 Unique per physical device, used in multi-device signal routing.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_my_user_lid())

    async def conn_get_my_user_wid(self) -> Any:
        """
        Type: RAM (AccountStore).
        Returns: str — full serialized Wid e.g. '919876543210@c.us' (same as user_id for personal accounts).
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_my_user_wid())

    async def conn_get_my_device_id(self) -> Any:
        """
        Type: RAM (AccountStore).
        Returns: int — linked device slot index (0 = primary phone, 1-4 = companion devices).
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_my_device_id())

    async def conn_is_online(self) -> bool:
        """
        Type: RAM (AppState — WebSocket stream flag).
        Returns: bool — True if the WS connection to Meta servers is active.
                 Observed: True when session is live.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_is_online())

    async def conn_is_multi_device(self) -> bool:
        """
        Type: RAM (AccountStore).
        Returns: bool — True if the account has multi-device mode enabled.
                 Observed: True for modern WhatsApp (all accounts post-2022 use MD).
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_is_multi_device())

    async def conn_is_idle(self) -> bool:
        """
        Type: RAM (AppState).
        Returns: bool — True if the session has been idle (no WS activity).
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_is_idle())

    async def conn_is_main_ready(self) -> bool:
        """
        Type: RAM (AppState).
        Returns: bool — True if WA Web has fully initialised (stores loaded, WS connected).
                 Use this as the readiness gate before making any API calls.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_is_main_ready())

    async def conn_get_platform(self) -> Any:
        """
        Type: RAM (BuildConstants).
        Returns: str — platform identifier.
                 Observed values: 'android', 'web', 'smbi' (SMB iOS), 'smba' (SMB Android).
                 'android' means the paired primary device is Android.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_platform())

    async def conn_get_theme(self) -> Any:
        """
        Type: RAM (ThemeStore).
        Returns: str — UI theme. Observed values: 'light', 'dark', 'default'.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_theme())

    async def conn_get_stream_data(self) -> Any:
        """
        Type: RAM (StreamStore — WebSocket connection state).
        Returns: dict with fields:
            mode  (str) — 'MAIN' | 'INIT' | 'OFFLINE'
            info  (str) — 'NORMAL' | 'PAUSED' | 'TIMEOUT'
        Observed: {'mode': 'MAIN', 'info': 'NORMAL'} on a live healthy session.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_stream_data())

    async def conn_get_build_constants(self) -> Any:
        """
        Type: RAM (BuildConstants — hardcoded in the WA Web bundle).
        Returns: dict with fields:
            VERSION_PRIMARY          (str) — major version e.g. '2'
            VERSION_SECONDARY        (str) — minor version e.g. '3000'
            VERSION_TERTIARY         (str) — build number e.g. '1035913242'
            VERSION_BASE             (str) — full version string '2.3000.1035913242'
            VERSION_STR              (str) — same as VERSION_BASE
            PUSH_PHASE               (str) — rollout phase e.g. 'C3'
            WINDOWS_BUILD            (str|None) — Windows desktop build if applicable
            WINDOWS_OFFLINE          (bool) — Windows offline mode flag
            VERSION_BASE_WITH_WINDOWS_BUILD (str) — combined version string
            DYN_ORIGIN               (str) — 'https://web.whatsapp.com/'
            WEB_PUBLIC_PATH          (str) — '/'
            BUILD_URL                (str) — 'https://web.whatsapp.com/'
            PARSED                   (dict) — {PRIMARY: int, SECONDARY: int, TERTIARY: int}
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_build_constants())

    async def conn_get_ab_props(self) -> Any:
        """
        Type: RAM (ABProps — A/B feature flags loaded at session init, no ongoing network cost).
        Returns: dict of str → Any — active feature flag overrides for this session.
                 Keys are internal WA experiment names (e.g. 'ab_send_delay_ms').
                 Empty dict if no active experiments.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_ab_props())

    async def conn_get_auto_download_settings(self) -> Any:
        """
        Type: RAM (SettingsStore).
        Returns: dict — media auto-download config, typically:
            photos    (bool)
            audio     (bool)
            video     (bool)
            documents (bool)
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_auto_download_settings())

    async def conn_get_history_sync_progress(self) -> Any:
        """
        Type: RAM (HistorySyncStore — populated after linking a new device).
        Returns: dict|None — sync progress object, or None if no sync is in progress.
                 Relevant only during the first few minutes of a new device link.
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_get_history_sync_progress())

    async def conn_needs_update(self) -> bool:
        """
        Type: RAM (AppState).
        Returns: bool|None — True if WA Web is stale and requires a page reload.
                 Observed: None when session is current (no update needed).
        """
        return await self._evaluate_stealth(WAJS_Scripts.conn_needs_update())

    # ─────────────────────────────────────────────
    # 8. CONTACT (READ)
    # ─────────────────────────────────────────────

    async def contact_get(self, contact_id: str) -> Dict[str, Any]:
        """
        Type: RAM (ContactStore — synchronous map lookup, zero network cost).
        NOTE: Your own ID will return {} — you are not stored in your own ContactStore.
              Use contact_id of someone in your address book.
        Returns: dict with fields:
            id_serialized   (str)  — '919876543210@c.us'
            name            (str)  — saved name in your address book
            pushname        (str)  — their WhatsApp display name
            shortName       (str)  — shortened display name
            type            (str)  — 'in' (in contacts) | 'out' (not saved)
            isBusiness      (bool) — whether this is a Business account
            isEnterprise    (bool)
            isMe            (bool) — True if this is your own ID
            isMyContact     (bool) — True if saved in phonebook
            isUser          (bool)
            isWAContact     (bool) — True if they have WhatsApp
            isPSA           (bool) — Public Service Announcement account
            verifiedName    (str|None) — business verified name
        """
        return await self._evaluate_stealth(WAJS_Scripts.contact_get(contact_id))

    async def contact_list(self, count: int = 20) -> List[Dict[str, Any]]:
        """
        Type: RAM (ContactStore — synchronous ES6 Map iteration).
        Returns: list of contact dicts (see contact_get for field reference).
        Args:
            count: Max contacts to return (default 20). Increase carefully —
                   large address books (500+) slow down the JS bridge.
        """
        return await self._evaluate_stealth(WAJS_Scripts.contact_list(count=count))

    async def contact_query_exists(self, contact_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — sends an XMPP presence/check packet to Meta servers.
              Use sparingly (<30/hr to avoid rate-flag).
        Returns: dict with fields:
            wid             (dict) — {server, user, _serialized} — their WhatsApp ID
            biz             (bool) — whether this is a Business account
            bizInfo         (dict|None) — business info if biz=True
            disappearingMode(dict) — {duration: int, settingTimestamp: int}
            status          (str)  — their current About text (may be empty)
            lid             (dict) — {server, user, _serialized} — linked device ID
        Returns None if the number does not have WhatsApp.
        """
        return await self._evaluate_stealth(WAJS_Scripts.contact_query_exists(contact_id))

    async def contact_get_profile_picture_url(self, contact_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — CDN HTTP request to fetch current profile picture URL.
        Returns: str — CDN URL like 'https://pps.whatsapp.net/v/...'
                 None if the contact has no picture or privacy blocks you.
        Observed: None when contact has default/no picture.
        """
        return await self._evaluate_stealth(
            WAJS_Scripts.contact_get_profile_picture_url(contact_id)
        )

    async def contact_get_status(self, contact_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — XMPP request to fetch their About/status text.
        Returns: str — their About text e.g. 'Hey there! I am using WhatsApp.'
                 Empty string if not set or privacy-blocked.
        Observed: ' ' (space) for accounts with empty about text.
        """
        return await self._evaluate_stealth(WAJS_Scripts.contact_get_status(contact_id))

    async def contact_get_business_profile(self, contact_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — HTTP request for WhatsApp Business profile data.
        Returns: dict with business fields (address, email, website, category, description)
                 None if the contact is not a Business account.
        """
        return await self._evaluate_stealth(WAJS_Scripts.contact_get_business_profile(contact_id))

    async def contact_get_common_groups(self, contact_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — XMPP query for shared group list.
        Returns: list of group ID strings e.g. ['120363401916939000@g.us', ...]
        """
        return await self._evaluate_stealth(WAJS_Scripts.contact_get_common_groups(contact_id))

    # ─────────────────────────────────────────────
    # 9. GROUP (READ)
    # ─────────────────────────────────────────────

    async def group_get_all(self) -> List[Dict[str, Any]]:
        """
        Type: RAM (ChatStore filter — zero network cost).
        Returns: list of group ChatModel dicts. Observed fields per group:
            id_serialized           (str)  — '120363401916939000@g.us'
            __x_name                (str)  — group display name
            __x_formattedTitle      (str)  — same as name
            __x_unreadCount         (int)  — unread message count
            __x_muteExpiration      (int)  — 0 if not muted, else Unix ts
            __x_isAutoMuted         (bool)
            __x_archive             (bool) — whether archived
            __x_isLocked            (bool) — admin-only send restriction
            __x_notSpam             (bool) — False = flagged by Meta
            __x_canSend             (bool) — whether you can send in this group
            __x_ephemeralDuration   (int)  — disappearing msg duration (0=off)
            __x_ephemeralSettingTimestamp (int)
            __x_isAnnounceGrpRestrict    (bool) — announcement-only group
            __x_isReadOnly          (bool)
            __x_trusted             (bool)
            __x_groupType           (str)  — 'DEFAULT' | 'COMMUNITY' | 'ANNOUNCEMENT'
            __x_hasCapi             (bool) — has Community API features
            __x_isParentGroup       (bool) — is a Community parent group
            __x_groupSafetyChecked  (bool)
            __x_msgsLength          (int)  — messages loaded in RAM
            __x_msgsChanged         (int)  — change counter
            __x_t                   (int)  — last activity Unix timestamp
            __x_pendingAction       (int)
            __x_unreadMentionCount  (int)
            __x_disappearingModeTrigger  (str) — 'chat_settings' | 'account'
            __x_disappearingModeInitiator (str)
            revisionNumber          (int)  — internal group metadata revision
            initialIndex            (int)  — sidebar position
            proxyName               (str)  — always 'chat'
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_get_all())

    async def group_get_participants(self, group_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — XMPP fetch from Meta servers. Can take 2–5s+.
              Use only when you need the live member list; avoid polling.
        Returns: list of participant dicts, each with:
            id_serialized (str) — participant WhatsApp ID
            isAdmin       (bool)
            isSuperAdmin  (bool)
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_get_participants(group_id))

    async def group_get_invite_code(self, group_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — XMPP request. Requires admin privileges.
        Returns: str — the invite code portion of the link
                 (full link = 'https://chat.whatsapp.com/<invite_code>')
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_get_invite_code(group_id))

    async def group_get_info_from_invite_code(self, invite_code: str) -> Any:
        """
        Type: NETWORK ⚠️ — XMPP fetch. Safe to call before joining.
        Returns: dict with group preview metadata:
            id_serialized  (str)  — group JID
            subject        (str)  — group name
            size           (int)  — current member count
            creation       (int)  — creation Unix timestamp
        """
        return await self._evaluate_stealth(
            WAJS_Scripts.group_get_info_from_invite_code(invite_code)
        )

    async def group_get_membership_requests(self, group_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — XMPP fetch. Only works if you are admin.
        Returns: list of pending join request dicts:
            id_serialized  (str) — requester's WhatsApp ID
            addedBy        (str) — who added them (if via invite link)
            requestTime    (int) — Unix timestamp of request
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_get_membership_requests(group_id))

    async def group_get_past_participants(self, group_id: str) -> Any:
        """
        Type: RAM (GroupMetadataStore — cached locally).
        Returns: list of past participant dicts:
            id_serialized  (str) — their WhatsApp ID
            leaveTs        (int) — Unix timestamp when they left
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_get_past_participants(group_id))

    async def group_i_am_admin(self, group_id: str) -> bool:
        """
        Type: RAM (GroupMetadataStore — local participant role lookup).
        Returns: bool — True if your ID is in the admin list of this group.
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_i_am_admin(group_id))

    async def group_i_am_super_admin(self, group_id: str) -> bool:
        """
        Type: RAM (GroupMetadataStore).
        Returns: bool — True if you are the group creator (super-admin).
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_i_am_super_admin(group_id))

    async def group_get_size_limit(self) -> Any:
        """
        Type: RAM (BuildConstants / ABProps).
        Returns: int — max participants for a group.
                 Standard: 1024. Communities announcement groups: 5000.
        """
        return await self._evaluate_stealth(WAJS_Scripts.group_get_size_limit())

    # ─────────────────────────────────────────────
    # 10. BLOCKLIST (READ)
    # ─────────────────────────────────────────────

    async def blocklist_all(self) -> List[Dict[str, Any]]:
        """
        Type: RAM (BlocklistStore — local list, no network cost).
        Returns: list of blocked contact dicts (same fields as contact_get).
                 Empty list if no contacts are blocked.
        """
        return await self._evaluate_stealth(WAJS_Scripts.blocklist_all())

    async def blocklist_is_blocked(self, contact_id: str) -> bool:
        """
        Type: RAM (BlocklistStore — O(1) set lookup).
        Returns: bool — True if the contact_id is in your block list.
        """
        return await self._evaluate_stealth(WAJS_Scripts.blocklist_is_blocked(contact_id))

    # ─────────────────────────────────────────────
    # 11. STATUS / STORIES (READ)
    # ─────────────────────────────────────────────

    async def status_get(self, contact_id: str) -> Any:
        """
        Type: NETWORK ⚠️ — fetches their Status from Meta's CDN/servers.
        Returns: list of Status story objects, each with:
            id_serialized  (str)  — message ID of the story
            type           (str)  — 'text' | 'image' | 'video'
            body           (str)  — text content (for text stories)
            t              (int)  — Unix timestamp of post
            mimetype       (str)  — media MIME type if media story
            isViewed       (bool) — whether you've viewed it
        Returns empty list if they have no active stories or privacy blocks you.
        """
        return await self._evaluate_stealth(WAJS_Scripts.status_get(contact_id))

    async def status_get_mine(self) -> Any:
        """
        Type: RAM (StatusStore — your own stories cached locally).
        Returns: list of your own Status story objects (same fields as status_get).
                 Empty list if you have no active stories.
        """
        return await self._evaluate_stealth(WAJS_Scripts.status_get_mine())

    # ─────────────────────────────────────────────
    # 12. PROFILE (READ)
    # ─────────────────────────────────────────────

    async def profile_get_my_name(self) -> Any:
        """
        Type: RAM (AccountStore).
        Returns: str — your WhatsApp display name as set in your profile settings.
        """
        return await self._evaluate_stealth(WAJS_Scripts.profile_get_my_name())

    async def profile_get_my_status(self) -> Any:
        """
        Type: RAM (AccountStore).
        Returns: str — your About text. Empty string if not set.
        """
        return await self._evaluate_stealth(WAJS_Scripts.profile_get_my_status())

    async def profile_get_my_picture(self) -> Any:
        """
        Type: RAM (AccountStore — locally cached URL).
        Returns: str — CDN URL for your own profile picture, or None if no picture.
        """
        return await self._evaluate_stealth(WAJS_Scripts.profile_get_my_picture())

    async def profile_is_business(self) -> bool:
        """
        Type: RAM (AccountStore).
        Returns: bool — True if this is a WhatsApp Business (SMBI/SMBA) account.
                 NOTE: platform='android' does NOT mean it's not Business;
                 check isBusiness separately.
        """
        return await self._evaluate_stealth(WAJS_Scripts.profile_is_business())

    # ─────────────────────────────────────────────
    # 13. PRIVACY (READ)
    # ─────────────────────────────────────────────

    async def privacy_get(self) -> Any:
        """
        Type: RAM (PrivacyStore — locally synced privacy settings).
        Returns: dict with fields:
            readreceipts    (str) — 'all' | 'none' (blue tick visibility)
            profile         (str) — 'all' | 'contacts' | 'contact_blacklist' | 'none'
            status          (str) — who can see your Status stories
            online          (str) — 'all' | 'match_last_seen'
            last            (str) — last seen visibility
            groupadd        (str) — who can add you to groups
        """
        return await self._evaluate_stealth(WAJS_Scripts.privacy_get())

    # ─────────────────────────────────────────────
    # 14. LABELS (READ) — Business accounts only
    # ─────────────────────────────────────────────

    async def labels_get_all(self) -> Any:
        """
        Type: RAM (LabelsStore — Business accounts only).
        Returns: list of label dicts, each with:
            id          (str) — label ID
            name        (str) — display name
            color       (int) — color palette index
            colorHex    (str) — hex color string e.g. '#FF6900'
            predefined  (bool) — True for WhatsApp built-in labels
        Returns empty list on non-Business accounts.
        """
        return await self._evaluate_stealth(WAJS_Scripts.labels_get_all())

    async def labels_get_by_id(self, label_id: str) -> Any:
        """
        Type: RAM (LabelsStore).
        Returns: single label dict (see labels_get_all for fields), or None if not found.
        """
        return await self._evaluate_stealth(WAJS_Scripts.labels_get_by_id(label_id))

    # ─────────────────────────────────────────────
    # 15. COMMUNITY (READ)
    # ─────────────────────────────────────────────

    async def community_get_subgroups(self, community_id: str) -> Any:
        """Child group chats of a Community."""
        return await self._evaluate_stealth(WAJS_Scripts.community_get_subgroups(community_id))

    async def community_get_participants(self, community_id: str) -> Any:
        """All members across a Community."""
        return await self._evaluate_stealth(WAJS_Scripts.community_get_participants(community_id))

    async def community_get_announcement_group(self, community_id: str) -> Any:
        """The admin broadcast/announcement group of a Community."""
        return await self._evaluate_stealth(
            WAJS_Scripts.community_get_announcement_group(community_id)
        )

    # ═══════════════════════════════════════════════════════════
    # ACTION-LEVEL — MUTATIONS & INTERACTIONS (OPTIONAL / TIER 3)
    # ═══════════════════════════════════════════════════════════

    # ─────────────────────────────────────────────
    # CONN (ACTIONS)
    # ─────────────────────────────────────────────

    async def conn_logout(self) -> Any:
        """Terminate the WhatsApp session."""
        return await self._evaluate_stealth(WAJS_Scripts.conn_logout())

    async def conn_mark_available(self) -> Any:
        """Appear as online/available."""
        return await self._evaluate_stealth(WAJS_Scripts.conn_mark_available())

    async def conn_set_keep_alive(self, enabled: bool = True) -> Any:
        """Prevent the session from going idle."""
        return await self._evaluate_stealth(WAJS_Scripts.conn_set_keep_alive(enabled))

    async def conn_refresh_qr(self) -> Any:
        """Force a fresh QR code to be generated (for QR login flows)."""
        return await self._evaluate_stealth(WAJS_Scripts.conn_refresh_qr())

    async def conn_set_theme(self, theme: str) -> Any:
        """Set UI theme. Values: 'default' (light) | 'dark'."""
        return await self._evaluate_stealth(WAJS_Scripts.conn_set_theme(theme))

    # ─────────────────────────────────────────────
    # CONTACT (ACTIONS)
    # ─────────────────────────────────────────────

    async def contact_subscribe_presence(self, contact_id: str) -> Any:
        """Start receiving real-time online/typing presence events for a contact."""
        return await self._evaluate_stealth(WAJS_Scripts.contact_subscribe_presence(contact_id))

    async def contact_unsubscribe_presence(self, contact_id: str) -> Any:
        """Stop receiving presence events for a contact."""
        return await self._evaluate_stealth(WAJS_Scripts.contact_unsubscribe_presence(contact_id))

    async def contact_save(self, contact_id: str, name: str) -> Any:
        """Save or update the display name for a contact."""
        return await self._evaluate_stealth(WAJS_Scripts.contact_save(contact_id, name))

    async def contact_remove(self, contact_id: str) -> Any:
        """Delete a contact from your address book."""
        return await self._evaluate_stealth(WAJS_Scripts.contact_remove(contact_id))

    async def contact_report(self, contact_id: str) -> Any:
        """Report a contact to Meta."""
        return await self._evaluate_stealth(WAJS_Scripts.contact_report(contact_id))

    # ─────────────────────────────────────────────
    # GROUP (ACTIONS)
    # ─────────────────────────────────────────────

    async def group_create(self, name: str, participants: List[str]) -> Any:
        """Create a new group chat."""
        return await self._evaluate_stealth(WAJS_Scripts.group_create(name, participants))

    async def group_add_participants(self, group_id: str, participants: List[str]) -> Any:
        """Add members to a group."""
        return await self._evaluate_stealth(
            WAJS_Scripts.group_add_participants(group_id, participants)
        )

    async def group_remove_participants(self, group_id: str, participants: List[str]) -> Any:
        """Remove members from a group."""
        return await self._evaluate_stealth(
            WAJS_Scripts.group_remove_participants(group_id, participants)
        )

    async def group_promote_participants(self, group_id: str, participants: List[str]) -> Any:
        """Promote members to admin."""
        return await self._evaluate_stealth(
            WAJS_Scripts.group_promote_participants(group_id, participants)
        )

    async def group_demote_participants(self, group_id: str, participants: List[str]) -> Any:
        """Remove admin from members."""
        return await self._evaluate_stealth(
            WAJS_Scripts.group_demote_participants(group_id, participants)
        )

    async def group_leave(self, group_id: str) -> Any:
        """Leave a group chat."""
        return await self._evaluate_stealth(WAJS_Scripts.group_leave(group_id))

    async def group_join(self, invite_code: str) -> Any:
        """Join a group via invite link code."""
        return await self._evaluate_stealth(WAJS_Scripts.group_join(invite_code))

    async def group_set_subject(self, group_id: str, name: str) -> Any:
        """Rename a group."""
        return await self._evaluate_stealth(WAJS_Scripts.group_set_subject(group_id, name))

    async def group_set_description(self, group_id: str, text: str) -> Any:
        """Set the group description."""
        return await self._evaluate_stealth(WAJS_Scripts.group_set_description(group_id, text))

    async def group_revoke_invite_code(self, group_id: str) -> Any:
        """Revoke the current invite link and generate a new one."""
        return await self._evaluate_stealth(WAJS_Scripts.group_revoke_invite_code(group_id))

    async def group_approve_membership(self, group_id: str, participants: List[str]) -> Any:
        """Approve pending join requests."""
        return await self._evaluate_stealth(
            WAJS_Scripts.group_approve_membership(group_id, participants)
        )

    async def group_reject_membership(self, group_id: str, participants: List[str]) -> Any:
        """Reject pending join requests."""
        return await self._evaluate_stealth(
            WAJS_Scripts.group_reject_membership(group_id, participants)
        )

    # ─────────────────────────────────────────────
    # BLOCKLIST (ACTIONS)
    # ─────────────────────────────────────────────

    async def blocklist_block(self, contact_id: str) -> Any:
        """Block a contact."""
        return await self._evaluate_stealth(WAJS_Scripts.blocklist_block(contact_id))

    async def blocklist_unblock(self, contact_id: str) -> Any:
        """Unblock a contact."""
        return await self._evaluate_stealth(WAJS_Scripts.blocklist_unblock(contact_id))

    # ─────────────────────────────────────────────
    # STATUS (ACTIONS)
    # ─────────────────────────────────────────────

    async def status_send_text(self, text: str, bg_color: Optional[str] = None) -> Any:
        """Post a text Status story."""
        return await self._evaluate_stealth(WAJS_Scripts.status_send_text(text, bg_color))

    async def status_send_read(self, msg_id: str) -> Any:
        """Mark a Status story as viewed."""
        return await self._evaluate_stealth(WAJS_Scripts.status_send_read(msg_id))

    async def status_remove(self, msg_id: str) -> Any:
        """Delete one of your own Status stories."""
        return await self._evaluate_stealth(WAJS_Scripts.status_remove(msg_id))

    # ─────────────────────────────────────────────
    # PROFILE (ACTIONS)
    # ─────────────────────────────────────────────

    async def profile_set_my_name(self, name: str) -> Any:
        """Change your WhatsApp display name."""
        return await self._evaluate_stealth(WAJS_Scripts.profile_set_my_name(name))

    async def profile_set_my_status(self, text: str) -> Any:
        """Change your About text."""
        return await self._evaluate_stealth(WAJS_Scripts.profile_set_my_status(text))

    async def profile_remove_my_picture(self) -> Any:
        """Remove your profile picture."""
        return await self._evaluate_stealth(WAJS_Scripts.profile_remove_my_picture())

    # ─────────────────────────────────────────────
    # PRIVACY (ACTIONS)
    # ─────────────────────────────────────────────

    async def privacy_set_last_seen(self, value: str) -> Any:
        """Who can see your Last Seen. Values: 'all'|'contacts'|'contact_blacklist'|'none'."""
        return await self._evaluate_stealth(WAJS_Scripts.privacy_set_last_seen(value))

    async def privacy_set_online(self, value: str) -> Any:
        """Who can see your Online status. Values: 'all'|'match_last_seen'."""
        return await self._evaluate_stealth(WAJS_Scripts.privacy_set_online(value))

    async def privacy_set_profile_pic(self, value: str) -> Any:
        """Who can see your profile picture."""
        return await self._evaluate_stealth(WAJS_Scripts.privacy_set_profile_pic(value))

    async def privacy_set_read_receipts(self, value: str) -> Any:
        """Enable/disable blue ticks. Values: 'all'|'none'."""
        return await self._evaluate_stealth(WAJS_Scripts.privacy_set_read_receipts(value))

    async def privacy_set_add_group(self, value: str) -> Any:
        """Who can add you to groups."""
        return await self._evaluate_stealth(WAJS_Scripts.privacy_set_add_group(value))

    async def privacy_set_status(self, value: str) -> Any:
        """Who can see your Status stories."""
        return await self._evaluate_stealth(WAJS_Scripts.privacy_set_status(value))

    # ─────────────────────────────────────────────
    # LABELS (ACTIONS) — Business accounts only
    # ─────────────────────────────────────────────

    async def labels_add_new(self, name: str, color: Optional[int] = None) -> Any:
        """Create a new label."""
        return await self._evaluate_stealth(WAJS_Scripts.labels_add_new(name, color))

    async def labels_delete(self, label_id: str) -> Any:
        """Delete a label."""
        return await self._evaluate_stealth(WAJS_Scripts.labels_delete(label_id))

    async def labels_apply(self, chat_id: str, label_ids: List[str]) -> Any:
        """Apply labels to a chat."""
        return await self._evaluate_stealth(WAJS_Scripts.labels_apply(chat_id, label_ids))

    # ─────────────────────────────────────────────
    # CALL (ACTIONS)
    # ─────────────────────────────────────────────

    async def call_offer(self, contact_id: str, is_video: bool = False) -> Any:
        """Initiate a voice or video call."""
        return await self._evaluate_stealth(WAJS_Scripts.call_offer(contact_id, is_video))

    async def call_accept(self, call_id: str) -> Any:
        """Accept an incoming call."""
        return await self._evaluate_stealth(WAJS_Scripts.call_accept(call_id))

    async def call_reject(self, call_id: str) -> Any:
        """Reject an incoming call."""
        return await self._evaluate_stealth(WAJS_Scripts.call_reject(call_id))

    async def call_end(self, call_id: str) -> Any:
        """End an active call."""
        return await self._evaluate_stealth(WAJS_Scripts.call_end(call_id))

    # ─────────────────────────────────────────────
    # COMMUNITY (ACTIONS)
    # ─────────────────────────────────────────────

    async def community_create(self, name: str, group_ids: List[str]) -> Any:
        """Create a new Community with existing groups."""
        return await self._evaluate_stealth(WAJS_Scripts.community_create(name, group_ids))

    async def community_deactivate(self, community_id: str) -> Any:
        """Deactivate / close a Community."""
        return await self._evaluate_stealth(WAJS_Scripts.community_deactivate(community_id))

    async def community_add_subgroups(self, community_id: str, group_ids: List[str]) -> Any:
        """Add groups to an existing Community."""
        return await self._evaluate_stealth(
            WAJS_Scripts.community_add_subgroups(community_id, group_ids)
        )

    async def community_remove_subgroups(self, community_id: str, group_ids: List[str]) -> Any:
        """Remove groups from a Community."""
        return await self._evaluate_stealth(
            WAJS_Scripts.community_remove_subgroups(community_id, group_ids)
        )
