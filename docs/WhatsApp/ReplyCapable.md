# ↩️ ReplyCapable: Targeted Conversations

The `ReplyCapable` class allows your bot to reply to specific messages in a chat. It uses human-like interactions (side-edge double-clicks) to trigger the reply UI in WhatsApp Web.

Like other WhatsApp modules, it operates as a **Singleton-per-Page Pattern**.

---

### 🛠️ Setting up ReplyCapable

To initialize, you need an active `page`, `logger`, and `WebSelectorConfig`.

```python
from camouchat.WhatsApp import ReplyCapable, WebSelectorConfig
from camouchat.camouchat_logger import CamouChatLogger

# Ensure UIConfig is ready
ui_config = WebSelectorConfig(page=page_obj, log=CamouChatLogger)

reply_handler = ReplyCapable(
    page=page_obj,
    # ------------- Required Parameter -------------

    log=CamouChatLogger,
    # ------------- Required Parameter -------------

    UIConfig=ui_config
    # ------------- Required Parameter -------------
)
```

---

### 📦 Key Functions

#### 1. `reply(message, humanize, text, **kwargs)`
Replies to a specific message object using humanized typing.

```python
from camouchat.WhatsApp import HumanizedOperations

# Initialize humanization for natural typing speeds
humanizer = HumanizedOperations(page=page_obj, log=camouchatLogger)

# Assuming 'msg' is a whatsapp_message object from MessageProcessor.Fetcher
success = await reply_handler.reply(
    message=msg,
    # ------------- Required Parameter -------------
    # The specific message object you want to reply to.
    
    humanize=humanizer,
    # ------------- Required Parameter -------------
    # Handles the natural typing simulation.
    
    text="This is a targeted reply! 🚀"
    # ------------- Required Parameter -------------
    # The response text.
)

if success:
    print("✅ Reply sent successfully!")
```

---

### 🛡️ How it works: Stealth Mechanics
1. **Edge Clicking**: Instead of a "bot-like" direct API call, it performs a double-click on the side edge of the message bubble (0.2x width for incoming, 0.8x for outgoing) to trigger the reply action, just like a human would.
2. **Natural Delays**: It incorporates random timing between clicks and typing to avoid detection by WhatsApp's behavioral analysis.

---

### 💡 Pro Tip
Always ensure the message you are replying to is visible in the viewport. The SDK attempts to `scroll_into_view_if_needed`, but for very long histories, it's best to fetch fresh messages before replying.
