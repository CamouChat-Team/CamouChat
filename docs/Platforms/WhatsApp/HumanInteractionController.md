# 🖱️ HumanInteractionController

`camouchat.WhatsApp.human_interaction_controller`

`HumanInteractionController` is the **typing simulation engine** of CamouChat. It handles all keyboard input to the browser in a way that mimics real human behavior — variable-speed character-by-character typing for short texts, clipboard-paste for long texts, and a reliable fallback fill strategy. It also manages OS-level clipboard access in a thread-safe way to prevent race conditions when multiple bots run concurrently.

Like all WhatsApp components, it enforces **Singleton-per-Page** binding.

---

## 🛠️ Constructor

```python
HumanInteractionController(
    page: Page,
    ui_config: WebUISelectorCapable,
    log: Optional[Union[Logger, LoggerAdapter]] = None,
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | `Page` | ✅ Yes | The active Playwright async page. All keyboard events are dispatched through this. |
| `ui_config` | `WebUISelectorCapable` | ✅ Yes | A `WebSelectorConfig` instance. Required by the base interface (used for locator context). |
| `log` | `Logger \| LoggerAdapter` | ❌ No | Logger for typing fallback events and clipboard warnings. |

```python
from camouchat.WhatsApp import HumanInteractionController, WebSelectorConfig
from camouchat.camouchat_logger import camouchatLogger

ui_config = WebSelectorConfig(page=page, log=camouchatLogger)

humanizer = HumanInteractionController(
    page=page,
    ui_config=ui_config,
    log=camouchatLogger,
)
```

---

## 📦 Methods

### `typing(text, **kwargs) → bool`

The primary typing method. Types text into the browser with human-like behavior, choosing the appropriate strategy based on text length.

| kwarg | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `ElementHandle \| Locator` | ✅ Yes | The DOM element to type into. An `ElementHandle` or `Playwright` `Locator`. |

```python
msg_box_handle = await ui_config.message_box().element_handle(timeout=1000)

success = await humanizer.type_text(
    text="Hello from CamouChat! 🤖",
    source=msg_box_handle,
)
```

Returns `True` if text was typed successfully. Falls back to `_Instant_fill()` on Playwright errors (e.g., element detached mid-type), which also returns `True` on success.

#### Typing Strategy Selection

| Text Length | Strategy |
|-------------|----------|
| ≤ 50 chars | `page.keyboard.type()` with 80–100 ms per-character delay |
| > 50 chars, multi-line | Per-line: lines ≤ 50 chars → `page.keyboard.type()`; lines > 50 chars → `_safe_clipboard_paste()`. Line breaks use `Shift+Enter`. |

> [!TIP]
> The 80–100 ms per-character delay is calibrated to the typical human typing speed of 40–50 WPM. Too-uniform delays at exactly the same interval are detectable as bots — the randomization makes the pattern statistically realistic.

---

### `_safe_clipboard_paste(text) → None` *(private)*

Safely copies `text` to the OS clipboard and pastes it into the active browser element using `Ctrl+V`. Designed for long text lines (>50 chars) where character-by-character typing would be too slow.

**Thread-safety**: Uses two layers of locking to prevent clipboard corruption when multiple bots run concurrently:
1. **`asyncio.Lock()`** — prevents concurrent async access within the same Python process.
2. **`FileLock`** (via `filelock`) — an OS-level file-based lock at `/tmp/whatsapp_clipboard.lock` — prevents concurrent access *across multiple Python processes* (i.e., multiple bot instances on the same machine).

The previous clipboard content is always restored after pasting, so user clipboard data is never permanently overwritten.

```
acquire asyncio lock
  acquire OS file lock
    save current clipboard
    copy text to clipboard
    sleep 50ms (propagation delay)
    press Ctrl+V
  release OS file lock
  restore previous clipboard
release asyncio lock
```

---

### `_ensure_clean_input(source, retries=3) → None` *(private)*

Before typing, checks if the target input element already has content (`inner_text()`). If it does, it performs `Ctrl+A` → `Backspace` to clear it. Retries up to 3 times with exponential backoff.

This is called automatically at the start of every `typing()` call to prevent new text from being appended to stale content.

---

### `_Instant_fill(text, source) → bool` *(private)*

Emergency fallback when `typing()` encounters a Playwright error (e.g., `TimeoutError`, element detachment). Uses Playwright's `source.fill(text)` which sets the value directly without simulating keyboard events, then presses `Enter`.

> [!WARNING]
> `_Instant_fill()` is less human-like than `typing()` — it sets the entire input value at once. It is only used as a fallback, never as the primary typing strategy. If it also fails, `HumanizedOperationError` is raised.

---

## 🔒 Clipboard Race Condition Protection

When running multiple bots simultaneously (e.g., 5 profiles, each with their own `HumanInteractionController`), they might all try to paste long messages at the same time. Without protection, one bot could overwrite another's clipboard content mid-paste.

The dual-lock system prevents this:

```python
# Simplified conceptual flow for concurrent bots:
# Bot 1: acquires asyncio lock → acquires file lock → pastes → releases
# Bot 2: waits for asyncio lock → waits for file lock → pastes → releases
# Bot 3: same...
```

> [!NOTE]
> The `filelock` library must be installed (`pip install filelock`). It is listed as a dependency in `requirements.txt`. The lock file is created at `tempfile.gettempdir() + "/whatsapp_clipboard.lock"`.

---

## 💡 Pro Tips

- **Always pass `source`**: The `source` kwarg is required — without it, `ElementNotFoundError` is raised immediately. Get it via `element_handle()` on a locator (as `InteractionController.reply()` does) or pass the `Locator` directly.
- **Long messages**: For messages over 50 characters, the clipboard paste strategy is used automatically. You don't need to worry about this — the strategy selection is internal.
- **`InteractionController` already handles this**: When you call `reply_handler.reply(..., humanize=humanizer, text="...")`, the humanizer's `typing()` is called internally. You don't need to call `humanizer.typing()` separately for replies.
