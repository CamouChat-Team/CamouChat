# WhatsApp QuickStart 💬

`camouchat.WhatsApp`

This guide walks you through a complete WhatsApp bot session — from first-time login through message extraction, replying, and sending media. Each step builds on the previous one.

---

## Prerequisites

Make sure you've completed the [BrowserManager QuickStart](../../BrowserManager/quickstart.md) and have:
- A `ProfileManager` instance (`pm`)
- A `ProfileInfo` object (`profile`)
- A running `CamoufoxBrowser` instance (`browser`)

---

## Step 1: Get a Page 🌐

```python
import asyncio
from camouchat.BrowserManager import CamoufoxBrowser, ProfileManager, Platform

pm = ProfileManager()
profile = pm.create_profile(Platform.WHATSAPP, "MyBot")

# ... (browser setup as in BrowserManager quickstart) ...

async def main():
    page = await browser.get_page()
```

---

## Step 2: Create WebSelectorConfig 🎯

`WebSelectorConfig` is the **single source of DOM selectors** for WhatsApp Web. Create one instance and share it across all WhatsApp components in the same session.

```python
from camouchat.WhatsApp import WebSelectorConfig
from camouchat.camouchat_logger import camouchatLogger

ui_config = WebSelectorConfig(page=page, log=camouchatLogger)
```

> [!TIP]
> `WebSelectorConfig` is bound to a specific `page` object. If you create a new page, create a new `WebSelectorConfig` for it.

---

## Step 3: Login (One-Time Setup) 🔐

Before any automation, you need to authenticate. This is only required once per profile — the session is saved in `profile.cache_dir`.

```python
from camouchat.WhatsApp import Login

login_obj = Login(
    page=page,
    UIConfig=ui_config,     # PascalCase parameter name
    log=camouchatLogger,
)

# Method 0: QR code (scan with your phone)
await login_obj.login(
    method=0,
    wait_time=150_000,      # 150 seconds to scan
)

# OR Method 1: Phone number pairing code
# await login_obj.login(
#     method=1,
#     number=9876543210,    # Without country code
#     country="India",      # Exactly as in WhatsApp's dropdown
# )

# Verify connection
if await login_obj.is_login_successful():
    print("✅ Logged in and connected!")
```

> [!NOTE]
> After the first successful login, subsequent runs will skip this step automatically — the session persists in the Camoufox cache directory.

---

## Step 4: Fetch Chats 📥

```python
from camouchat.WhatsApp import ChatProcessor

chat_proc = ChatProcessor(
    page=page,
    ui_config=ui_config,    # snake_case parameter name
    log=camouchatLogger,
)

# Get the top 5 chats from the sidebar
chats = await chat_proc.fetch_chats(limit=5, retry=5)

for chat in chats:
    unread = await ChatProcessor.is_unread(chat)
    status = "📩 UNREAD" if unread else "✓ read"
    print(f"  {status} | {chat.chat_name}")
```

---

## Step 5: Process Messages 📝

```python
from camouchat.WhatsApp import MessageProcessor

# Basic setup — no storage or filter (in-memory only)
msg_proc = MessageProcessor(
    chat_processor=chat_proc,
    page=page,
    ui_config=ui_config,
    # storage_obj=storage,  # Add SQLAlchemyStorage for persistence
    # filter_obj=msg_filter, # Add MessageFilter for rate-limiting
    # encryption_key=key,   # Add for AES-256 encryption
    log=camouchatLogger,
)

# Fetch messages from the first chat
messages = await msg_proc.fetch_messages(chat=chats[0], retry=3)

# Separate by direction
inbound = await MessageProcessor.sort_messages(messages, incoming=True)
outbound = await MessageProcessor.sort_messages(messages, incoming=False)

print(f"Received {len(inbound)} messages, sent {len(outbound)}.")
for msg in inbound:
    print(f"  [{msg.id_serialized}] {msg.raw_data}")
```

> [!TIP]
> Use `only_new=True` kwarg in `fetch_messages()` for event-driven bots — it returns only messages not yet in the database, so you process each message exactly once.

---

## Step 6: Add Persistence & Encryption 💾🔐

For production bots, you need async database storage and optionally AES-256 encryption:

```python
import asyncio
from camouchat.StorageDB import SQLAlchemyStorage
from camouchat.Filter import MessageFilter

queue = asyncio.Queue()

# Initialize storage from profile (uses profile.database_url automatically)
storage = SQLAlchemyStorage.from_profile(profile=profile, queue=queue, log=camouchatLogger)

# Initialize rate-limit filter
msg_filter = MessageFilter(
    LimitTime=3600,               # Hard-drop chats deferred > 1 hour
    Max_Messages_Per_Window=10,   # Max 10 messages per 60-second window
    Window_Seconds=60,
)

# Load or generate encryption key
if pm.is_encryption_enabled(Platform.WHATSAPP, "MyBot"):
    key = pm.get_key(Platform.WHATSAPP, "MyBot")
else:
    key = pm.enable_encryption(Platform.WHATSAPP, "MyBot")

async with storage:   # Starts DB, creates tables, starts background writer
    msg_proc = MessageProcessor(
        chat_processor=chat_proc,
        page=page,
        ui_config=ui_config,
        storage_obj=storage,
        filter_obj=msg_filter,
        encryption_key=key,
        log=camouchatLogger,
    )

    messages = await msg_proc.fetch_messages(chat=chats[0], only_new=True)
    print(f"Stored {len(messages)} new messages.")
```

---

## Step 7: Reply to a Message ↩️

```python
from camouchat.WhatsApp import ReplyCapable, HumanInteractionController

humanizer = HumanInteractionController(
    page=page,
    ui_config=ui_config,
    log=camouchatLogger,
)

reply_handler = ReplyCapable(
    page=page,
    ui_config=ui_config,    # snake_case here too
    log=camouchatLogger,
)

# Reply to the latest inbound message
if inbound:
    success = await reply_handler.reply(
        message=inbound[-1],
        humanize=humanizer,
        text="Hey! I received your message. 🤖",
    )
    if success:
        print("✅ Reply sent!")
```

---

## Step 8: Send a Media File 📎

```python
from camouchat.WhatsApp import MediaCapable
from camouchat.Interfaces.media_capable_interface import MediaType, FileTyped

media_handler = MediaCapable(
    page=page,
    UIConfig=ui_config,     # PascalCase for MediaCapable
    log=camouchatLogger,
)

success = await media_handler.add_media(
    mtype=MediaType.IMAGE,
    file=FileTyped(
        uri="/absolute/path/to/report.png",
        name="report.png",
        mime_type="image/png",
    ),
)

if success:
    # add_media returns True when the file is staged — press Enter to send
    await page.keyboard.press("Enter")
    print("📤 Image sent!")
```

---

## Parameter Name Reference Card

Different components use slightly different naming conventions for the same concept:

| Component | UI Config param | 
|-----------|----------------|
| `Login` | `UIConfig` (PascalCase) |
| `MediaCapable` | `UIConfig` (PascalCase) |
| `ChatProcessor` | `ui_config` (snake_case) |
| `ReplyCapable` | `ui_config` (snake_case) |
| `MessageProcessor` | `ui_config` (snake_case) |
| `HumanInteractionController` | `ui_config` (snake_case) |

---

## Pro-Tips for Production ⚡

- **Session reuse**: Once logged in, the bot never calls `login()` again on the same profile (unless the session expires or gets revoked).
- **`only_new=True`**: Essential for polling bots — avoids reprocessing already-stored messages.
- **Encryption key rotation**: Do not call `enable_encryption()` twice on the same profile — it raises `ValueError`. Use `get_key()` on all subsequent runs.
- **Multi-bot concurrency**: Each profile runs in its own `CamoufoxBrowser` instance. The 2nd+ browser is automatically headless — perfect for running 10+ bots silently.

For detailed method references, see:
- [Login Guide](Login.md) | [ChatProcessor Guide](ChatProcessor.md) | [MessageProcessor Guide](MessageProcessor.md)
- [ReplyCapable Guide](ReplyCapable.md) | [MediaCapable Guide](MediaCapable.md)
- [HumanInteractionController Guide](HumanInteractionController.md)
