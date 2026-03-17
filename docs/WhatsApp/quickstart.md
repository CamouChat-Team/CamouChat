# WhatsApp QuickStart Guide 💬

Building a WhatsApp bot with **CamouChat** is designed to be intuitive and stealth-first. This guide covers authentication, chat management, and message processing.

---

### Step 1: Authentication (One-Time Setup) 🔐

To start, link your WhatsApp account to your sandboxed profile. You can choose between **QR Code** or **Phone Number** methods.

```python
import asyncio
from camouchat.WhatsApp import Login, WebSelectorConfig
from camouchat.camouchat_logger import CamouChatLogger


async def setup_whatsapp(page):
    # ui_config_obj is the Core heart of the camouchat to talk to WhatsApp
    ui_config_obj = WebSelectorConfig(page=page, log=CamouChatLogger)

    # Initialize the Login handler
    login_obj = Login(
        # Need 3 Parameter --- all 3 are REQUIRED PARAMETER -------
        page=page,
        # We Support Asyncio only.
        UIConfig=ui_config_obj,
        log=CamouChatLogger,
    )

    await login_obj.login(
        method=0,
        # ---- REQUIRED PARAMETER ------
        # 0 FOR QR BASED LOGIN.
        # 1 FOR CODE BASED LOGIN.
        wait_time=150000,
        # ---- REQUIRED PARAMETER ------
        # The time it would wait for QR SCAN to be scanned
        url="https://web.whatsapp.com",
        # ----------- THE BELOW ARE ONLY REQUIRED WHEN YOU CHOOSE 1 AS YOUR LOGIN METHOD -------------
        number=0000000000,
        # ---- REQUIRED PARAMETER (if method=1) ------
        country="Your Country",
        # ---- REQUIRED PARAMETER (if method=1) ------
    )

    # Verify if login was successful
    if await login_obj.is_login_successful():
        print("✅ Logged in successfully!")

# asyncio.run(setup_whatsapp(page))
```

---

### Step 2: Fetching Conversations with ChatProcessor 📥

The `ChatProcessor` allows you to explore the sidebar and interact with visible chats.

```python
from camouchat.WhatsApp import ChatProcessor


async def manage_chats(page):
    ui_config = WebSelectorConfig(page=page, log=camouchatLogger)

    # All 3 are REQUIRED PARAMETER for ChatProcessor
    chat_proc = ChatProcessor(
        page=page,
        log=camouchatLogger,
        ui_config=ui_config
    )

    # Fetch visible chats
    # Returns list of whatsapp_chat
    _chats = await chat_proc.fetch_chats(limit=5)

    for chat in _chats:
        print(f"💬 Found Chat: {chat.chat_name}")
```

---

### Step 3: Processing and Storing Messages 📝

The `MessageProcessor` extracts history and optionally persists it to a database.

```python
from camouchat.WhatsApp import MessageProcessor


async def capture_messages(page, chat_proc):
    ui_config = WebSelectorConfig(page=page, log=camouchatLogger)

    # Initialize the Message Processor
    msg_proc = MessageProcessor(
        storage_obj=None,  # Optional: SQLAlchemyStorage instance to auto-save
        filter_obj=None,  # Optional: MessageFilter to drop certain types
        chat_processor=chat_proc,
        page=page,
        log=camouchatLogger,
        ui_config=ui_config
    )

    # Get a list of chats first
    _chats = await chat_proc.fetch_chats(limit=1)
    if _chats:
        target_chat = _chats[0]

        # Fetch, store, and filter messages from this chat
        messages = await msg_proc.fetch_messages(chat=target_chat, retry=3)

        for msg in messages:
            print(f"[{msg.direction}] {msg.raw_data}")


---

### Step 4: Advanced Operations (Replying & Media) 🚀

Expand
your
bot
's capabilities with targeted replies and file uploads.

```python
from camouchat.WhatsApp import ReplyCapable, MediaCapable, HumanizedOperations
from camouchat.Interfaces.media_capable_interface import MediaType, FileTyped


async def advanced_ops(page, chat_proc, target_chat):
    ui_config = WebSelectorConfig(page=page, log=camouchatLogger)
    humanizer = HumanizedOperations(page=page, log=camouchatLogger)

    # Replying to a message
    reply_handler = ReplyCapable(page=page, log=camouchatLogger, UIConfig=ui_config)
    # assuming 'target_msg' was fetched from msg_proc.Fetcher
    await reply_handler.reply(message=target_msg, humanize=humanizer, text="I received your message!")

    # Sending an image
    media_handler = MediaCapable(page=page, log=camouchatLogger, UIConfig=ui_config)
    await media_handler.add_media(
        mtype=MediaType.IMAGE,
        file=FileTyped(uri="/absolute/path/to/image.png")
    )
```

> [!NOTE]
> For in-depth details, see [ReplyCapable Guide](./ReplyCapable.md) and [MediaCapable Guide](./MediaCapable.md).
```

---

### Pro-Tips for WhatsApp Automation ⚡

- **Wait Times**: QR scan time defaults to 180s. Adjust `wait_time` if you need more.
- **Persistence**: Once logged in, your session is saved in the profile's disk cache. 
- **Stealth**: Avoid "inhuman" speeds. The SDK includes natural delays, but it's best to fetch messages only when needed.

For complete message encryption details, check the [MessageProcessor Documentation](./MessageProcessor.md).
