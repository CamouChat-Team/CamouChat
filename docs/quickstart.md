# ⚡ Quick Start

This guide covers basic and advanced examples to help you get started with the new **CamouChat** architecture quickly featuring the Profile Manager, Sandboxing, and Async DB integrations.

## Basic: Fetch Chats

```python
import asyncio
from camouchat.BrowserManager import ProfileManager, BrowserConfig, CamoufoxBrowser, Platform
from camouchat.BrowserManager.browserforge_manager import BrowserForgeCompatible
from camouchat.WhatsApp.login import Login
from camouchat.WhatsApp.chat_processor import ChatProcessor
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig
from camouchat.camouchat_logger import logger


async def main():
    # 1. Initialize Profile Manager and Create/Load Profile
    pm = ProfileManager()
    profile = pm.create_profile(Platform.WHATSAPP, "my_session")

    # 2. Configure Browser (Anti-detect Fingerprints mapped to your screen)
    fg_manager = BrowserForgeCompatible(log=logger)
    config = BrowserConfig(
        platform=Platform.WHATSAPP,
        locale="en-US",
        enable_cache=True,
        headless=False,
        fingerprint_obj=fg_manager
    )

    # 3. Launch Camoufox using Profile
    browser = CamoufoxBrowser(config=config, profile=profile, log=logger)
    page = await browser.get_page()

    # 4. Activate Profile (Handles Session Tracking & Locks)
    pm.activate_profile(Platform.WHATSAPP, "my_session", browser)

    # 5. Initialize UI config and Login
    ui_config = WebSelectorConfig(page=page, log=logger)
    login = Login(page=page, UIConfig=ui_config, log=logger)

    # Login (method=0 for QR, method=1 for Phone)
    # Scan QR code on first run!
    await login.login(method=0)

    # 6. Fetch chats
    chat_processor = ChatProcessor(page=page, UIConfig=ui_config, log=logger)
    async for chat, name in chat_processor.Fetcher(MaxChat=5):
        print(f"📂 Chat: {name}")

    # 7. Close gracefully and clean up profile lock
    await pm.close_profile(Platform.WHATSAPP, "my_session")


if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced: Message Processing with Encrypted SQLAlchemy Storage

```python
import asyncio
from camouchat.BrowserManager import ProfileManager, BrowserConfig, CamoufoxBrowser, Platform
from camouchat.BrowserManager.browserforge_manager import BrowserForgeCompatible
from camouchat.WhatsApp.login import Login
from camouchat.WhatsApp.chat_processor import ChatProcessor
from camouchat.WhatsApp.message_processor import MessageProcessor
from camouchat.WhatsApp.web_ui_config import WebSelectorConfig
from camouchat.StorageDB import SQLAlchemyStorage
from camouchat.camouchat_logger import logger


async def main():
    # 1. Profile Setup
    pm = ProfileManager(app_name="CamouChat")
    profile = pm.create_profile(Platform.WHATSAPP, "secure_session")

    # 2. Enable AES-256 Storage Encryption (Optional but highly recommended)
    if not pm.is_encryption_enabled(Platform.WHATSAPP, "secure_session"):
        encryption_key = pm.enable_encryption(Platform.WHATSAPP, "secure_session")
        logger.info("🔑 Encryption Enabled!")
    else:
        encryption_key = pm.get_key(Platform.WHATSAPP, "secure_session")
        logger.info("🔑 Encryption Key Retrieved from profile")

    # 3. Init Browser & Activate Profile
    fg_manager = BrowserForgeCompatible(log=logger)
    config = BrowserConfig(
        platform=Platform.WHATSAPP,
        locale="en-US",
        enable_cache=True,
        headless=False,
        fingerprint_obj=fg_manager
    )

    browser = CamoufoxBrowser(config=config, profile=profile, log=logger)
    page = await browser.get_page()
    pm.activate_profile(Platform.WHATSAPP, "secure_session", browser)

    # 4. Login
    ui_config = WebSelectorConfig(page=page, log=logger)
    login = Login(page=page, UIConfig=ui_config, log=logger)
    await login.login(method=0)

    # 5. Configure Async SQLAlchemy Storage using Profile path
    queue = asyncio.Queue()
    storage = SQLAlchemyStorage.from_profile(profile=profile, queue=queue, log=logger)

    async with storage:
        # Initialize processors
        chat_processor = ChatProcessor(page=page, UIConfig=ui_config, log=logger)
        msg_processor = MessageProcessor(
            page=page,
            UIConfig=ui_config,
            chat_processor=chat_processor,
            log=logger,
            storage=storage,  # Auto flush messages locally 
            encryption_key=encryption_key  # Inject AES-256 key
        )

        # 6. Fetch and process messages
        async for chat, name in chat_processor.Fetcher(MaxChat=3):
            print(f"\n📂 Processing: {name}")

            # Fetcher automatically deduplicates and inserts into async queue
            messages = await msg_processor.Fetcher(chat=chat, retry=3)

            for msg in messages:
                print(f"   💬 {msg.data_type}: {msg.raw_data[:50]}...")
                print(f"      ID: {msg.message_id}")

    # 7. Cleanup
    await pm.close_profile(Platform.WHATSAPP, "secure_session")


if __name__ == "__main__":
    asyncio.run(main())
```
