import json


class WAJS_Scripts:
    """
    The Vault: Contains all raw JavaScript execution strings for Playwright injection.
    All strings are wrapped in strict asynchronous Try-Catch blocks to prevent UI
    crashes and telemetry leaks to Meta.
    """

    @staticmethod
    def wrap_stealth_execution(js_code: str) -> str:
        """
        Wraps raw WPP JavaScript code in a try/catch.
        Returns a standardized JSON format back to the Python bridge.
        Formatted as an IIFE for Camoufox Main World execution.
        """
        return f"""
        (async () => {{
            try {{
                const res = await {js_code};
                return {{ status: 'success', data: res }};
            }} catch (err) {{
                return {{ status: 'error', message: err.toString() }};
            }}
        }})()
        """

    # --- 1. CORE & CONNECTION ---
    @classmethod
    def is_ready(cls) -> str:
        """Check if wa-js has finished hijacking Webpack"""
        return "window.WPP?.isReady === true"

    @classmethod
    def is_authenticated(cls) -> str:
        """Authentication script"""
        return cls.wrap_stealth_execution("WPP.conn.isAuthenticated()")

    # --- 2. CHAT & DATA FETCHING ---
    @classmethod
    def get_chat(cls, chat_id: str) -> str:
        """Fetch metadata for a specific chat"""
        return cls.wrap_stealth_execution(f"WPP.chat.get('{chat_id}')")

    @classmethod
    def get_messages(cls, chat_id: str, count: int = 50) -> str:
        """Fetch history from active RAM"""
        return cls.wrap_stealth_execution(
            f"WPP.chat.getMessages('{chat_id}', {{ count: {count} }})"
        )

    # --- 3. ACTIONS (TIER 3 FALLBACKS) ---
    @classmethod
    def send_text_message(cls, chat_id: str, message: str) -> str:
        """Pure API message sending"""
        # We must escape newlines/quotes in Python before sending to JS
        safe_msg = json.dumps(message)
        return cls.wrap_stealth_execution(f"WPP.chat.sendTextMessage('{chat_id}', {safe_msg})")

    @classmethod
    def mark_is_read(cls, chat_id: str) -> str:
        return cls.wrap_stealth_execution(f"WPP.chat.markIsRead('{chat_id}')")

    # --- 4. EVENTS (THE PUSH ARCHITECTURE) ---
    @classmethod
    def setup_new_message_listener(cls, python_alias: str) -> str:
        """
        Injects the bridge that pushes new WS messages directly to the Python handler.
        Formatted as IIFE for Main World execution.
        """
        return f"""
        (() => {{
            if (window._camou_has_listener) return;
            window.WPP.on('chat.new_message', (msg) => {{
                // Fire the Playwright-exposed python function
                window.{python_alias}(msg);
            }});
            window._camou_has_listener = true;
            return true;
        }})()
        """
