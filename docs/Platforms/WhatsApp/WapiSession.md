# 🌐 WapiSession & Managers

`camouchat.WhatsApp.api.WapiSession`

The `WapiSession` is the new core bridge connecting your Python application directly to WhatsApp's internal React/Redux memory state (Main World execution context). 

It replaces the old legacy DOM scrapers (`ChatProcessor`, `MessageProcessor`) entirely and provides instantaneous, stealth-safe data extraction without moving the user's screen or triggering visual read receipts randomly.

## ⚠️ Important Note on Method Types
Every method in the API managers is tagged with its execution risk profile:
*   🟢 **[Type: RAM]**: **100% Safe.** Reads directly from React's client-side memory without ever touching Meta's servers. Highly recommended for all stealth extraction.
*   🟢 **[Type: CDP]**: **Safe.** Simulates physical OS-level mouse/keyboard commands.
*   🟢 **[Type: INDEX DB]**: **Safe.** Reads directly from the local hard drive's browser cache.
*   **🚨 [Type: NETWORK]**: **DANGER / EXPERIMENTAL.** Sends an encoded WebSocket payload directly to WhatsApp's servers, completely bypassing the User Interface. **Only use for debugging, experimental headless bots, or high-risk "Tier 3" interactions.** Abusing these methods without emulating typing/reading delays *will* result in account bans.

---

## 🛠️ Initialization

```python
from camouchat.WhatsApp.api import WapiSession

wapi = WapiSession(page=page)
```

The session automatically initializes two domain-specific managers for you:
1. **`wapi.chat_manager`** (Instance of `ChatApiManager`)
2. **`wapi.message_manager`** (Instance of `MessageApiManager`)

---

## 💬 ChatApiManager

`wapi.chat_manager` allows you to retrieve chat models instantly. Under the hood, it triggers stealthy `window.Store.Chat.get()` operations within the JS bridge.

### Methods

#### `open_chat(chat: ChatModelAPI, page: Page) -> bool`
🟢 **[Type: CDP / RAM Fallback]**
The most advanced **Stealth Hybrid** method for forcibly opening a chat on screen.
*   **Step 1: Physical Bounding Box Search (Primary Stealth)**: It natively restricts search to the unmounted `div#pane-side` or `aria-label="Chat list"` DOM regions for `chat.formattedTitle`. If found on the active screen, it logs physical telemetry by drawing a `Camoufox` bezier curve to the bounding rectangle, taking ~1.5s, and emitting an OS-level layout point click.
*   **Step 2: Virtualized RAM Bridging (Fallback)**: If the chat is scrolled out of the current viewport, rather than frantically scrolling the page, it performs an ambient pointer move to generate safe noise, sleeps for natural reaction time (~2 seconds), and explicitly pushes WhatsApp's exact internal event router (`WPP.chat.openChatBottom()`).

#### `get_chat_by_id(chat_id: str) -> ChatModelAPI`
🟢 **[Type: RAM]**
Instantly fetches a specific chat by its formatted `jid`.

#### `get_chat_list(...) -> list[ChatModelAPI]`
🟢 **[Type: RAM]**
Rips the entire Chat array from RAM. Highly performant alternative to scrolling the left panel visually. Supports massive filtering:
*   `only_unread=True`, `only_groups=True`, `only_communities=True`
*   `count=50`, `with_labels=[...]`

#### `mark_is_read(chat_id: str)`
🚨 **[Type: NETWORK]**
Force-mark a chat as read. Sends a literal network read-receipt to WhatsApp servers instantly.

---

## ✉️ MessageApiManager

`wapi.message_manager` performs discrete message lookups, rapid disk extractions, and media decryption.

### Methods

#### `get_message_by_id(msg_id: str) -> MessageModelAPI | None`
🟢 **[Type: RAM]**
Instantly fetch any historical or current message by its `id_serialized`.

#### `get_messages(chat_id: str, count: int, ...) -> List[MessageModelAPI]`
🟢 **[Type: RAM]**
Pulls a list of messages from a specific chat entirely from React memory. 
You can filter by `media="image"`, `only_unread=True`, or fetch history using `anchor_msg_id`.

#### `get_unread(chat_id: str) -> List[MessageModelAPI]`
🟢 **[Type: RAM]**
Convenience shorthand for fetching only unread messages in a chat from memory.

#### `extract_media(message: MessageModelAPI, save_path: str) -> dict`
🟢 **[Type: RAM / NETWORK Fallback]**
Zero-telemetry media extractor. Attempts to pull the decrypted image/video/audio payload entirely from the browser's local Cache API using the E2E `mediaKey`. If the cache was flushed, it safely falls back to downloading the blob directly from Meta's CDNs.

#### `indexdb_get_messages(min_row_id: int, limit: int) -> List[MessageModelAPI]`
🟢 **[Type: INDEX DB]**
Global extraction. Reads raw sequential messages stored on the user's hard drive regardless of what chat they belong to. Perfect for massive database syncing.

#### `send_text_message(chat_id: str, message: str)`
🚨 **[Type: NETWORK]**
Pure API text send. Bypasses the Playwright UI, bypassing actual human typing, and fires the payload directly via WebSocket. Use at your own risk.
