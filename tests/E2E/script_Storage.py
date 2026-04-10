import asyncio
import traceback

from camouchat.BrowserManager import (
    BrowserConfig,
    BrowserForge,
    CamoufoxBrowser,
    Platform,
    ProfileManager,
)
from camouchat.StorageDB import SQLAlchemyStorage, StorageType
from camouchat.WhatsApp import Login, WebSelectorConfig
from camouchat.WhatsApp.api import WapiSession
from camouchat.WhatsApp.api.models import MessageModelAPI
from camouchat.WhatsApp.decorator import msg_event_hook


async def main():
    # ── Setup Storage (Once) ───────────────────────────────────────────────
    pm = ProfileManager()
    profile = pm.create_profile(
        platform=Platform.WHATSAPP, profile_id="Work", storage_type=StorageType.SQLITE
    )
    # Initialize storage once outside the loop
    storage = SQLAlchemyStorage.from_profile(profile=profile, queue=asyncio.Queue())
    await storage.start()

    save_ids = []
    msgs_batch = []

    # ── Browser & Login ────────────────────────────────────────────────────
    browser_forge = BrowserForge()
    config = BrowserConfig.from_dict(
        {
            "platform": Platform.WHATSAPP,
            "headless": False,
            "fingerprint_obj": browser_forge,
        }
    )
    browser = CamoufoxBrowser(config=config, profile=profile)
    page = await browser.get_page()
    ui = WebSelectorConfig(page=page)
    login = Login(page=page, UIConfig=ui)
    await login.login(method=0)

    # ── Event Hook ─────────────────────────────────────────────────────────
    wapi = WapiSession(page=page)

    @msg_event_hook(wapi_session=wapi)
    async def new_msg(msg: MessageModelAPI):
        print("New Msg Arrived with type--")
        print(msg)

        save_ids.append(msg.id_serialized)
        msgs_batch.append(msg)

    await new_msg()

    try:
        print("\n>>> Listening for messages... Press Ctrl+C to stop and view data from DB.")
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        # 1. Batch insert everything collected during the session
        await storage._insert_batch_internally(msgs=msgs_batch)

        # 2. Fetch ONLY the specific messages we just saved using the new method
        db_msgs = await storage.get_messages_by_ids_async(message_ids=save_ids)

        print("\n\n" + "=" * 50)
        print(f"DATABASE VERIFICATION: {len(db_msgs)} records retrieved by target IDs.")
        print("=" * 50)

        for msg in db_msgs:
            body = msg.get("body") or ""
            if len(body) > 100:
                body_disp = f"{body[:40]}...[truncated {len(body)} chars]"
            else:
                body_disp = body

            print("\n--- Found DB Record ---")
            print(f"ID     : {msg.get('id_serialized')}")
            print(f"DB Id  : {msg.get('id')}")
            print(f"Type   : {msg.get('msgtype')}")
            print(f"Body   : {body_disp}")
            print(f"FromMe : {msg.get('fromMe')}")
            print(f"ChatID : {msg.get('chat_id')}")
            print(f"Time   : {msg.get('timestamp')}")
            print(f"Created: {msg.get('created_at')}")
            print(f"E-Nonce: {msg.get('encryption_nonce')}")
            print("-----------------------")

        import os

        await CamoufoxBrowser.close_browser_by_pid(os.getpid())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception:
        traceback.print_exc()
