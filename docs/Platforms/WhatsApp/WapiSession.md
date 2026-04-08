# 🌐 WapiSession & Managers

`camouchat.WhatsApp.api.WapiSession`

The `WapiSession` is the new core bridge connecting your Python application directly to WhatsApp's internal React/Redux memory state (Main World execution context). 

It replaces the old legacy DOM scrapers (`ChatProcessor`, `MessageProcessor`) entirely and provides instantaneous, stealth-safe data extraction without moving the user's screen or triggering visual read receipts randomly.

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

#### `get_chat_by_id(jid: str) -> ChatModelAPI | None`
Instantly fetches a specific chat by its formatted `jid`.
```python
chat = await wapi.chat_manager.get_chat_by_id("1234567890@c.us")
if chat:
    print(f"Chat Name: {chat.name}")
    print(f"Unread Count: {chat.unreadCount}")
```

#### `get_all_chats() -> List[ChatModelAPI]`
Returns the entire list of initialized chats residing in memory. Highly performant alternative to scrolling the left panel visually.

#### `get_active_chat() -> ChatModelAPI | None`
Returns the `ChatModelAPI` representation of the chat currently open on the user's screen.

#### `open_chat(chat: ChatModelAPI, page: Page) -> bool`
The most advanced **Stealth Hybrid** method for forcibly opening a chat on screen.
*   **Step 1: Physical Bounding Box Search (Primary Stealth)**: It natively restricts search to the unmounted `div#pane-side` or `aria-label="Chat list"` DOM regions for `chat.formattedTitle`. If found on the active screen, it logs physical telemetry by drawing a `Camoufox` bezier curve to the bounding rectangle and emitting an OS-level layout point click.
*   **Step 2: Virtualized RAM Bridging (Fallback)**: If the chat is scrolled out of the current viewport (React virtualized unmount), rather than frantically scrolling the page like a classic bot, it performs an ambient pointer move to generate safe noise, sleeps for natural reaction time (~2 seconds), and explicitly pushes WhatsApp's exact internal event router (`WPP.chat.openChatBottom()`).

## ✉️ MessageApiManager

`wapi.message_manager` performs discrete message lookups (though for reading *incoming* messages in real time, see the `@msg_event_hook` documentation).

### Methods

#### `get_message_by_id(msg_id: str) -> MessageModelAPI | None`
Instantly fetch any historical or current message by its `id_serialized`. Bypasses DOM lookups completely.

```python
msg = await wapi.message_manager.get_message_by_id("false_1234567890@c.us_3EB012345678")
if msg:
    print(f"Historical Message Body: {msg.body}")
```
