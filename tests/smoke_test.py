"""
Smoke Test File to test every module before pushing to release.
"""
import asyncio
from asyncio import Queue
from typing import List

from camouchat.BrowserManager import (
    BrowserConfig,
    Platform,
    BrowserForgeCompatible,
    ProfileManager,
    CamoufoxBrowser
)
from camouchat.Filter import MessageFilter
from camouchat.StorageDB import SQLAlchemyStorage, StorageType
from camouchat.WhatsApp import (
    Login,
    WebSelectorConfig,
    ChatProcessor, MessageProcessor,
)
from camouchat.WhatsApp.models import Chat, Message
from camouchat.camouchat_logger import camouchatLogger


async def main():
    """The main function to run."""
    # 1. Profile
    pm = ProfileManager()
    profile = pm.create_profile(
        platform=Platform.WHATSAPP,
        profile_id="Work",
        storage_type=StorageType.SQLITE
    )

    # --- ENCRYPTION SETUP ---
    # 1.1 Check if encryption is enabled, if not enable it.
    # Note: enable_encryption returns the raw 32-byte AES key.
    try:
        if not profile.encryption.get("enabled"):
            print("Encryption not enabled for this profile. Enabling now...")
            enc_key = pm.enable_encryption(Platform.WHATSAPP, "Work")
        else:
            print("Encryption already enabled. Loading key...")
            enc_key = pm.get_key(Platform.WHATSAPP, "Work")
    except Exception as e:
        print(f"Encryption setup failed: {e}")
        enc_key = None

    # 2. Browser Config
    browser_forge = BrowserForgeCompatible()

    config = BrowserConfig.from_dict({
        "platform": Platform.WHATSAPP,
        "locale": "en-US",
        "enable_cache": False,
        "headless": False,
        "fingerprint_obj": browser_forge,
    })

    # 3. Browser
    browser = CamoufoxBrowser(
        config=config,
        profile=profile,
        log=camouchatLogger,
    )

    page = await browser.get_page()

    # 4. UI Config
    ui = WebSelectorConfig(page=page, log=camouchatLogger)

    # 5. Login (QR first time)
    login = Login(page=page, UIConfig=ui, log=camouchatLogger)

    await login.login(
        method=0  # [QR]
    )

    # 6. Chat Fetch
    chat_processor = ChatProcessor(
        page=page,
        log=camouchatLogger,
        ui_config=ui,
    )
    storage = SQLAlchemyStorage.from_profile(profile=profile, queue=Queue(), log=camouchatLogger)
    M_filter = MessageFilter()  # Using Default setup , LimitTime = 3600, MaxMessagePerWindow = 10 , Window_Seconds = 60

    print("Fetching chats...\n")
    message_processor = MessageProcessor(
        page=page,
        log=camouchatLogger,
        storage_obj=storage,
        ui_config=ui,
        chat_processor=chat_processor,
        filter_obj=M_filter,
        encryption_key=enc_key  # Passing the AES key here
    )


    from camouchat.WhatsApp import ReplyCapable
    reply_obj = ReplyCapable(page=page, ui_config=ui)

    from camouchat.WhatsApp import HumanInteractionController
    op = HumanInteractionController(page=page, ui_config=ui)

    processed = set()
    print(f"Profile path = [{profile.profile_dir}]")
    print(f"Database URL = [{profile.database_url}]")

    async with storage:
        for _ in range(50):
            chats: List[Chat] = await chat_processor.fetch_chats(limit=4)  # Top 4 chats fetched
            for chat in chats:
                print(chat)
                print("---Entering MessageProcessor...\n")
                # Using only_new=True to skip processed history.
                messages: List[Message] = await message_processor.fetch_messages(chat=chat, only_new=True)
                for msg in messages:
                    print(msg)
                    print("---------")
                    if msg.message_id not in processed:
                        if msg.raw_data == "camouchat-hi":  # Reply Back
                            do_rep = await reply_obj.reply(message=msg, humanize=op, text="Hi From CamouChat")
                            if do_rep:
                                print(f"Success ---- Replied for {msg.raw_data}  ********** ")
                            else:
                                print(f"Failed ❌❌❌❌❌❌❌  ---- Replied for {msg.raw_data} ❌❌❌❌❌❌❌❌  ")
                        if msg.raw_data == "shut-down":
                            do_rep = await reply_obj.reply(message=msg, humanize=op, text="Shutting Down ....")
                            if do_rep:
                                print(f"Success ---- Replied for {msg.raw_data}  ********** ")

                                print(f"Profile path = [{profile.profile_dir}]")
                                return
                            else:
                                print("Failed shutdown.")
                        processed.add(msg.message_id)  # Saves
            await asyncio.sleep(2)

        # --- VERIFY DECRYPTION ---
        if enc_key:
            print("\n--- Verifying Storage Decryption ---")
            # Fetch last 5 messages from DB and decrypt them using the same key
            decrypted_rows = await storage.get_decrypted_messages_async(key=enc_key, limit=5)
            for row in decrypted_rows:
                status = "Encrypted" if row.get('encryption_nonce') else "Plaintext"
                print(f"[{status}] Chat: {row.get('parent_chat_name')} | Body: {row.get('raw_data')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
