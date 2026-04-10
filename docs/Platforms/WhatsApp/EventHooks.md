# ⚡ Event Hooks & Message Architecture

The `v0.7.0` update introduces a paradigm shift in how messages are intercepted. Instead of relying on slow, fragile DOM scraping (`MessageProcessor`), CamouChat now utilizes a high-performance **RAM-level DOM Bridge** powered by `WapiSession` and the `@msg_event_hook` decorator.

This architecture intercepts payloads directly from WhatsApp's memory in real time, drastically improving stealth, speed, and data fidelity.

---

## 🛠️ The `@msg_event_hook` Decorator

The event hook system allows you to build asynchronous, event-driven bots effortlessly. It normalizes incoming raw payloads into strictly typed `MessageModelAPI` objects.

### Basic Implementation

```python
import asyncio
from camouchat.BrowserManager import Config, CamoufoxBrowser, ProfileManager
from camouchat.WhatsApp import Login, WebSelectorConfig
from camouchat.WhatsApp.api import WapiSession
from camouchat.WhatsApp.decorator import msg_event_hook
from camouchat.WhatsApp.api.models import MessageModelAPI


async def main():
    # 1. Initialize Profile & Browser (Skipped for brevity)
    ...

    # 2. Login
    ui = WebSelectorConfig(page=page)
    login = Login(page=page, UIConfig=ui)
    await login.login(method=0)

    # 3. Initialize the RAM Bridge
    wapi = WapiSession(page=page)

    # 4. Define the Event Hook
    @msg_event_hook(wapi)
    async def on_message_received(msg: MessageModelAPI):
        print("────────────────────────────────────────")
        print(f"📩 New Message from: {msg.jid_From}")
        print(f"💬 Body: {msg.body}")
        print(f"🏷️ Type: {msg.msgtype}")

        # You can use wapi to fetch extended chat info instantly
        chat_info = await wapi.chat_manager.get_chat_by_id(msg.jid_From)
        if chat_info:
            print(f"👤 Chat Name: {chat_info.name}")

    # 5. Start listening
    await on_message_received()

    # Keep the script running
    await asyncio.sleep(86400)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📦 Extracted Data Fidelity

Because messages are extracted from RAM, the `MessageModelAPI` class contains comprehensive metadata that was previously impossible to scrape from the DOM:

- `optionalAttrList`: Hidden attributes, message timestamps, and deep linking metadata.
- `mentionedJidList`: Easily parse user tags and mentions.
- `MsgType`: Accurately identifies `image`, `video`, `audio`, `document`, and `poll` payloads.
- **Media Keys**: Direct access to `mediaKey` and `directPath` for stealthy CDN blob decryption.

> [!TIP]
> **Why is this better?** The old DOM scraping method was prone to rate limits, visual errors, and required constant scrolling. The Event Hook operates entirely in the background, consuming zero visual state on the page, allowing your browser to remain completely undisturbed.

---

## 🔄 Replacing `MessageProcessor`

While `MessageProcessor` remains in the codebase for legacy compatibility, **all future implementations should migrate to `WapiSession` and `@msg_event_hook`**. 
Storage deduplication and DB logging can now be executed manually inside your decorated hook function perfectly securely.
