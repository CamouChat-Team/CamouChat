"""
Here we will be testing the new Msg Event Hook based Architecture Prototyping.
"""

import asyncio

from camouchat.BrowserManager import (
    BrowserConfig,
    BrowserForge,
    CamoufoxBrowser,
    Platform,
    ProfileManager,
)
from camouchat.contracts.media_capable import FileTyped, MediaType
from camouchat.StorageDB import StorageType
from camouchat.WhatsApp import Login, MediaCapable, WebSelectorConfig


async def main():
    # ── 1. Profile ─────────────────────────────────────────────────────────────
    pm = ProfileManager()
    profile = pm.create_profile(
        platform=Platform.WHATSAPP,
        profile_id="Work",
        storage_type=StorageType.SQLITE,
    )

    # ── 2. Browser ─────────────────────────────────────────────────────────────
    browser_forge = BrowserForge()
    config = BrowserConfig.from_dict(
        {
            "platform": Platform.WHATSAPP,
            "locale": "en-US",
            "enable_cache": False,
            "headless": False,
            "fingerprint_obj": browser_forge,
            "geoip": False,
        }
    )
    browser = CamoufoxBrowser(config=config, profile=profile)
    page = await browser.get_page()

    # ── 3. Login (reuses session) ───────────────────────────────────────────────
    ui = WebSelectorConfig(page=page)
    login = Login(page=page, UIConfig=ui)
    await login.login(method=0)  # Auto Handles saved Persistance.

    # ── 4. Message event hook ───────────────────────────────────────────────────
    from camouchat.WhatsApp.api import WapiSession
    from camouchat.WhatsApp.api.models import MessageModelAPI
    from camouchat.WhatsApp.decorator import msg_event_hook
    from camouchat.WhatsApp.features.human_interaction_controller import (
        HumanInteractionController,
    )
    from camouchat.WhatsApp.features.interaction_controller import ReplyCapable

    wapi = WapiSession(page=page)
    replyObj = ReplyCapable(page=page, ui_config=ui, wapi=wapi)
    media = MediaCapable(page=page, UIConfig=ui, wapi=wapi, profile=profile)
    hum = HumanInteractionController(page=page, ui_config=ui)

    @msg_event_hook(wapi_session=wapi)  # Pass the Wapi Session object here
    async def new_msg(msg: MessageModelAPI):
        print("\n --------- New Msg Arrived ───────────────────────────────────")
        print(msg, "\n")

        print(f"--------------Opening the Chat where msg came from : {msg.jid_From}")
        chat = await wapi.chat_manager.get_chat_by_id(msg.jid_From)  # get chatData
        print("Chat ---")
        print(chat)
        await wapi.chat_manager.open_chat(chat=chat)
        print(
            f"----------------Chat Opened name = {chat.formattedTitle} , id = {chat.id_serialized} \n"
        )

        # Process the msg Commands by some dummy commands.
        if msg.body == "!ping":
            print(f"[*] Command triggered: !ping from {msg.jid_From}")
            # await replyObj.quote_only(message=msg)  # UI: Trigger the quote/reply bubble
            await hum.send_api_text(
                chat_id=msg.jid_From,
                bridge=wapi.bridge,
                text="**You have been Ponged!!!** \ud83c\udfd3\n_Reply from CamouChat Stealth Bridge_",
                quoted_msg_id=msg.id_serialized,
            )

        elif msg.body == "!info":
            print(f"[*] Command triggered: !info from {msg.jid_From}")
            # Tests ChatModelAPI and dynamic metadata extraction
            # await replyObj.quote_only(message=msg)
            info_text = (
                f"\ud83d\udcdd *Chat Info*\n"
                f"\u2022 Title: {chat.formattedTitle}\n"
                f"\u2022 JID: {chat.id_serialized}\n"
                f"\u2022 Unread: {chat.unreadCount}\n"
                f"\u2022 Is Group: {chat.groupType}\n"
                f"\u2022 Is Archived: {chat.isArchived}\n"
            )
            await hum.send_api_text(
                bridge=wapi.bridge,
                text=info_text,
                chat_id=msg.jid_From,
                quoted_msg_id=msg.id_serialized,
            )

        elif msg.body == "!me":
            print("[*] Command triggered: !me (Identity Extraction)")
            # Tests identity and sender objects
            sender_name = getattr(msg.senderObj, "formattedName", "Unknown")
            push_name = getattr(msg.senderObj, "pushname", "Unknown")
            # await replyObj.quote_only(message=msg)
            await hum.send_api_text(
                chat_id=msg.jid_From,
                bridge=wapi.bridge,
                text=f"\ud83d\udc64 *Identity Profile*\n\u2022 Name: {sender_name}\n\u2022 PushName: {push_name}",
            )

        elif msg.body and msg.body.startswith("!echo "):
            print("[*] Command triggered: !echo (Humanized Interaction)")
            echo_text = msg.body.replace("!echo ", "")
            await replyObj.reply(
                message=msg, humanize=hum, text=f"Echo: {echo_text}"
            )  # Directly use native typing.
        elif msg.body and msg.body == "!media":
            print("[*] Command triggered: !media — requesting test image upload")
            await hum.send_api_text(
                chat_id=msg.jid_From,
                bridge=wapi.bridge,
                text="📎 Send me any image, video, or audio to test media save+resend.",
            )

        elif msg.msgtype in (
            "image",
            "video",
            "audio",
            "ptt",
            "document",
            "sticker",
            "gif",
        ):
            print(f"[*] Media message received — type={msg.msgtype}")

            # 1. Save to disk (WPP managed local-first download)
            saved_path = await media.save_media(message=msg)

            if not saved_path:
                print("[!] save_media returned None — media could not be retrieved.")
                await hum.send_api_text(
                    chat_id=msg.jid_From,
                    bridge=wapi.bridge,
                    text=f"⚠️ Could not retrieve media (type={msg.msgtype}).",
                )
                return

            print(f"[✔] Media saved → {saved_path}")

            # 2. Re-upload the saved file back to the same chat
            wa_type = msg.msgtype or "document"
            if wa_type in ("image", "sticker"):
                mtype = MediaType.IMAGE
            elif wa_type in ("video", "gif"):
                mtype = MediaType.VIDEO
            elif wa_type in ("audio", "ptt"):
                mtype = MediaType.AUDIO
            else:
                mtype = MediaType.DOCUMENT

            import os

            file_name = os.path.basename(saved_path)
            file_obj = FileTyped(uri=saved_path, name=file_name, mime_type=msg.mimetype)

            print(f"[*] Re-uploading {file_name} as {mtype} to {msg.jid_From}")
            resend_ok = await media.add_media(
                mtype=mtype, file=file_obj, force=True
            )  # Force it cuz we customly adding then sending.
            if resend_ok:
                print("[✔] Media re-sent successfully.")
            else:
                print("[!] add_media returned False — re-send may have failed.")

    # Keep the script running to listen for events
    await new_msg()
    print("\n[\u2714] Hook active. Try sending !ping, !info, !me, or !echo <text> in WhatsApp.")
    await asyncio.sleep(3600)  # 1 hour running.


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()
