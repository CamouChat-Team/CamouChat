# ↩️ InteractionController

`camouchat.WhatsApp.reply_capable`

`InteractionController` allows your bot to **reply to a specific message** in a chat by triggering WhatsApp's native reply UI. Instead of using a direct API call (which would look bot-like), it simulates the human behavior of double-clicking on the edge of a message bubble — the exact gesture WhatsApp Web uses to open the reply composer.

Like all WhatsApp components, it enforces **Singleton-per-Page** binding.

---

## 🛠️ Constructor

```python
InteractionController(
    page: Page,
    ui_config: WebSelectorConfig,
    log: Optional[Union[Logger, LoggerAdapter]] = None,
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | `Page` | ✅ Yes | The active Playwright async page. All interactions (CDP click, keyboard, input box) happen here. |
| `ui_config` | `WebSelectorConfig` | ✅ Yes | Provides the `message_box()` locator for the reply input field. Note: parameter name is `ui_config` (snake_case). |
| `log` | `Logger \| LoggerAdapter` | ❌ No | Logger for click attempts and typing. |

```python
from camouchat.WhatsApp import InteractionController, WebSelectorConfig, HumanInteractionController
from camouchat.camouchat_logger import camouchatLogger

ui_config = WebSelectorConfig(page=page, log=camouchatLogger)
humanizer = HumanInteractionController(page=page, ui_config=ui_config, log=camouchatLogger)

reply_handler = InteractionController(
    page=page,
    ui_config=ui_config,
    log=camouchatLogger,
)
```

---

## 📦 Methods

### `reply(message, humanize, text, **kwargs) → bool`

Replies to a specific `Message` object using `HumanInteractionController` for typed input.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | `Message` | ✅ Yes | The target `Message` object from `MessageProcessor.fetch_messages()`. Must have a valid `data_id` attribute. |
| `humanize` | `HumanInteractionController` | ✅ Yes | Handles the natural typing simulation. Required to avoid bot-marker uniform typing speeds. |
| `text` | `str \| None` | ✅ Yes | The reply text to type. If `None` or empty string, the input box is clicked but nothing is typed. |

```python
# Fetch messages first
messages = await msg_proc.fetch_messages(chat=chats[0])

# Reply to the first received message
inbound = await MessageProcessor.sort_messages(messages, incoming=True)

if inbound:
    success = await reply_handler.reply(
        message=inbound[0],
        humanize=humanizer,
        text="Thanks for your message! 🤖",
    )
    if success:
        print("✅ Reply sent!")
```

Returns `True` if the text was successfully typed and `Enter` was pressed. Returns `False` if the humanizer's typing method returned `False`.

> [!NOTE]
> After typing, `page.keyboard.press("Enter")` is called automatically by `reply()`. You do **not** need to press Enter separately.

---

## 🛡️ How `_side_edge_click()` Works

`reply()` internally calls `_side_edge_click(message)` to open the reply composer. This private method is the anti-detection core of the reply flow:

**Why not just use Playwright's `locator.click()`?**  
WhatsApp Web uses a virtual scroll — message nodes are mounted and unmounted from the DOM as you scroll. Playwright's standard `scroll_into_view_if_needed()` internally snapshots an `ElementHandle`, but WhatsApp re-renders the node mid-action, causing "not attached to DOM" errors.

**The CDP approach**:
1. Uses `page.evaluate()` with raw JavaScript to call `el.scrollIntoView()` and `getBoundingClientRect()` — both bypass the Playwright `ElementHandle` chain entirely.
2. Calculates the click x-coordinate as **20% from the left** for incoming messages and **80% from the left** (i.e., 20% from the right) for outgoing, mirroring the natural position humans double-click to reply.
3. Issues a `page.mouse.click()` with `click_count=2` and a random delay of 55–70 ms between clicks.
4. Retries up to **20 times** with 1-second gaps — covering the brief window when WhatsApp re-renders a node to update message status ticks (✓ → ✓✓).

```python
# Internal only — shown for documentation purposes
# Click position is determined by message direction:
is_incoming = (message.direction == "IN")
rel_x = dims["width"] * (0.2 if is_incoming else 0.8)
```

---

## 🔔 Error Handling

All failures raise `InteractionControllerError` from `camouchat.Exceptions.whatsapp`:

| Scenario | Exception Message |
|----------|------------------|
| `message` is `None` or has no `data_id` | `"Message or data_id is missing."` |
| Message not found in DOM after 20 retries | `"side_edge_click failed after 20 attempts."` |
| Input box click timed out | `"reply timed out while preparing input box"` |

```python
from camouchat.Exceptions.whatsapp import InteractionControllerError

try:
    await reply_handler.reply(message=msg, humanize=humanizer, text="Pong!")
except InteractionControllerError as e:
    print(f"Reply failed: {e}")
```

---

## 💡 Pro Tips

- **Message visibility**: `_side_edge_click()` scrolls the target message into view via JavaScript before clicking. However, for very long chat histories (thousands of messages), it is still best practice to call `fetch_messages()` close to your reply action so the message node is likely near the bottom of the visible area.
- **`data_id` is required**: `reply()` locates the message element using `div[data-id="..."]` in the DOM. If a `Message` object has a `None` or empty `data_id`, `InteractionControllerError` is raised immediately. Always verify messages from `fetch_messages()` are complete before replying.
- **HumanInteractionController dependency**: You must create a `HumanInteractionController` instance and pass it to `reply()`. The humanizer handles the fine-motor simulation of variable-speed typing so the reply pattern doesn't match bot behavior profiles.
