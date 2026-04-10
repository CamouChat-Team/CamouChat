# 💬 ChatProcessor (Legacy)

> [!WARNING]
> **Legacy Architecture:** `ChatProcessor` relies on slow, fragile DOM scraping and scrolling to extract chat data. For high-performance, real-time extraction, please use the new `WapiSession.chat_manager` to access chats instantly from RAM.

`camouchat.WhatsApp.chat_processor`

`ChatProcessor` manages the WhatsApp Web sidebar — fetching visible chats, clicking into them, checking unread status, and marking them as unread. It is the entry point for all chat-level interactions before you dive into messages.

All methods are async and use **Singleton-per-Page** binding: one `ChatProcessor` instance per `Page` object, automatically garbage-collected when the page closes.

---

## 🛠️ Constructor

```python
ChatProcessor(
    page: Page,
    ui_config: WebSelectorConfig,
    log: Optional[Union[Logger, LoggerAdapter]] = None,
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | `Page` | ✅ Yes | The active Playwright async page. Used for all DOM queries and CDP mouse events. |
| `ui_config` | `WebSelectorConfig` | ✅ Yes | Provides all DOM selectors for chat list items, names, unread badges, and menus. Note: this uses `ui_config` (lowercase), unlike `Login`/`MediaCapable` which use `UIConfig`. |
| `log` | `Logger \| LoggerAdapter` | ❌ No | Logger for retry messages and click debugging. |

```python
from camouchat.WhatsApp import ChatProcessor, WebSelectorConfig
from camouchat.camouchat_logger import camouchatLogger

ui_config = WebSelectorConfig(page=page, log=camouchatLogger)

chat_proc = ChatProcessor(
    page=page,
    ui_config=ui_config,
    log=camouchatLogger,
)
```

---

## 📦 Methods

### `fetch_chats(limit=5, retry=5, **kwargs) → Sequence[Chat]`

Scrapes the sidebar chat list and returns a sequence of `Chat` objects, each wrapping a live DOM `Locator`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | `int` | `5` | Maximum number of chats to return. Scoped to visible items in the sidebar. |
| `retry` | `int` | `5` | Number of retry attempts if the sidebar hasn't rendered yet. 1-second sleep between tries. |

```python
chats = await chat_proc.fetch_chats(limit=10, retry=5)

for chat in chats:
    print(f"💬 {chat.name}")
```

`Chat` objects have two key attributes:
- `chat_name` (`str`): The display name of the chat.
- `chat_ui` (`Locator`): The live DOM locator for the chat row.

> [!NOTE]
> `fetch_chats` raises `ChatNotFoundError` (from `camouchat.Exceptions.whatsapp`) if no chats are visible after all retries. This typically means WhatsApp Web hasn't finished loading or the account is not connected.

---

### `is_unread(chat) → int` *(static)*

Inspects the unread badge element (`[aria-label*='unread']`) on a chat row and returns `1` if there is an unread message count, `0` otherwise.

```python
status = await ChatProcessor.is_unread(chats[0])

if status == 1:
    print("📩 Unread messages!")
```

> [!NOTE]
> Returns `1` only when a numeric count is present in the badge span. A chat pinned at the top without a count badge returns `0`.

---

### `do_unread(chat) → bool`

Right-clicks the chat row to open the context menu, then clicks **"Mark as unread"** if available. If the chat is already marked unread, it logs the state and returns `True` without error.

```python
success = await chat_proc.do_unread(chats[0])
# → True if the context menu action was performed or chat was already unread
```

**Use case**: After processing messages in a chat, mark it unread again so your monitoring logic picks it up in the next cycle if needed.

---

### `_click_chat(chat, **kwargs) → bool` *(semi-private)*

Opens a chat by injecting a **CDP raw mouse click** at the chat row's center coordinates via JavaScript `getBoundingClientRect()`. This bypasses Playwright's actionability checks, which can deadlock when WhatsApp's virtual-scroll re-renders the sidebar.

| kwarg | Type | Default | Description |
|-------|------|---------|-------------|
| `retries` | `int` | `20` | Max click attempts before raising `ChatClickError`. |
| `base_delay` | `float` | `1.0` | Seconds to wait between retry attempts. |

> [!NOTE]
> You rarely call `_click_chat()` directly. `MessageProcessor.fetch_messages()` calls it automatically via the `@ensure_chat_clicked` decorator before scraping messages.

---

## 🛡️ Singleton Pattern & Memory Safety

```python
# All three lines return the same instance for the same page
cp1 = ChatProcessor(page=page, ui_config=ui_config, log=log)
cp2 = ChatProcessor(page=page, ui_config=ui_config, log=log)
assert cp1 is cp2   # True
```

The instance registry uses `weakref.WeakKeyDictionary[Page, ChatProcessor]`. When the Playwright `Page` is closed and garbage-collected, the `ChatProcessor` is automatically removed from the registry — no manual cleanup required.

---

## 🔔 Exception Hierarchy

All exceptions raised by `ChatProcessor` are subclasses of `ChatError` → `WhatsAppError`:

| Exception | Source |
|-----------|--------|
| `ChatNotFoundError` | `fetch_chats()` when sidebar is empty after retries. |
| `ChatProcessorError` | General extraction failure after max retries. |
| `ChatClickError` | `_click_chat()` exhausted all retries. |
| `ChatUnreadError` | `is_unread()` / `do_unread()` DOM interaction failure. |
| `ChatMenuError` | `do_unread()` cannot find the context menu application. |

---

## 💡 Pro Tips

- **Scroll visibility**: `fetch_chats` only returns chats currently rendered in the sidebar DOM. For bots that need to process older chats, scroll the sidebar first before fetching.
- **Large `limit` values**: WhatsApp Web virtualizes the sidebar, so chats beyond what's rendered are not in the DOM. A `limit` larger than what's visible on screen may return fewer results than requested — this is expected behavior.
- **CDP click reliability**: The `_click_chat` implementation uses slight random jitter (`±2px`) on top of the calculated coordinates to mimic natural mouse landing variance.
