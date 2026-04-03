# BrowserManager QuickStart 🚀

`camouchat.BrowserManager`

The `BrowserManager` module is the foundation of **CamouChat**. It handles profile creation, browser fingerprinting, and the full Camoufox lifecycle. Follow these steps to launch an isolated, stealth browser session.

---

## Step 1: Initialize the ProfileManager 🗃️

The `ProfileManager` is your disk-backed registry of all browser identities. Creating a profile sets up an isolated directory with its own cache, database, and fingerprint file.

```python
from camouchat.BrowserManager import ProfileManager, Platform

pm = ProfileManager()

# Idempotent — creates the profile on first call, returns existing on subsequent calls
profile = pm.create_profile(
    platform=Platform.WHATSAPP,     # Required — determines the directory namespace
    profile_id="MarketingBot",      # Required — your human-readable profile name
)

print(f"✅ Profile ready at: {profile.profile_dir}")
print(f"   DB URL:           {profile.database_url}")
```

> [!TIP]
> Each `profile_id` maps to a fully isolated directory. `"MarketingBot"` and `"SupportBot"` will never share cookies, fingerprints, or message history — even if they run simultaneously on the same machine.

---

## Step 2: Generate a BrowserForge Fingerprint 🧬

`BrowserForgeCompatible` generates a browser fingerprint that matches your machine's actual screen resolution (within 10% tolerance) and persists it to `fingerprint.pkl`. On subsequent runs, it reloads the saved fingerprint to maintain a **consistent browser identity** across sessions.

```python
from camouchat.BrowserManager import BrowserForge

bf = BrowserForge()

# get_fg() is called internally by CamoufoxBrowser at launch time.
# You don't need to call it manually — just pass the bf instance to BrowserConfig.
```

> [!NOTE]
> The fingerprint is always scoped to a profile via `bf.get_fg(profile=profile)`. Internally, if no fingerprint exists yet (empty `fingerprint.pkl`), it generates one. On subsequent runs, it loads the saved fingerprint. This consistency is what prevents "new device" detection on WhatsApp.

---

## Step 3: Configure the Browser ⚙️

`BrowserConfig` holds all the Camoufox launch parameters. Use `from_dict()` for a clean configuration dictionary pattern.

```python
from camouchat.BrowserManager import BrowserConfig

config = BrowserConfig.from_dict({
    "platform": Platform.WHATSAPP,
    # Required — tags this config with the target platform.

    "locale": "en-US",
    # Browser locale / Accept-Language header. Match your actual region.

    "headless": False,
    # False = invisible browser (recommended for production).
    # True = visible browser window (useful for initial login / debugging).
    # Note: ProfileManager.activate_profile() auto-sets this to True
    # if another profile is already running.

    "enable_cache": False,
    # False = fresh DOM on every page load (recommended for production).
    # True = reuse cached resources (useful for debugging slow connections).

    "geoip": True,
    # Auto-spoof geolocation, timezone, and language matching the IP address.
    # Highly recommended when using proxies to avoid detection mismatch.

    "proxy": {
        "server": "http://your-residential-proxy.com:22225",
        "username": "customer-abc-res-residential",
        "password": "yourpassword123",
    },
    # Optional — Residential proxies are recommended for the best stealth.
    # Camoufox uses this to route traffic and verify your target geolocation.

    "fingerprint_obj": bf,
    # Pass the BrowserForgeCompatible INSTANCE (not the generated Fingerprint).
    # The browser calls get_fg(profile) internally at launch time.

    "prefs": {},
    # Raw Firefox user preferences. Keep {} for stealth — custom prefs are detectable.

    "addons": [],
    # List of absolute paths to .xpi / .zip extension files to load on launch.
})
```

---

## Step 4: Launch the Camoufox Browser 🦊

Everything comes together in `CamoufoxBrowser`. It manages the full async browser lifecycle: launch, page creation, and cleanup.

```python
import asyncio
from camouchat.BrowserManager import CamoufoxBrowser
from camouchat.camouchat_logger import camouchatLogger

browser = CamoufoxBrowser(
    config=config,      # BrowserConfig we built above
    profile=profile,    # The sandboxed ProfileInfo
    log=camouchatLogger # Optional — defaults to camouchatLogger if omitted
)

async def start_session():
    # get_page() auto-launches the browser if not already running.
    # Reuses an existing blank tab to avoid unnecessary tab proliferation.
    page = await browser.get_page()
    await page.goto("https://web.whatsapp.com")
    print("🌐 Stealth browser is live!")

asyncio.run(start_session())
```

---

## Step 5: Activate the Profile (Optional but Recommended) ✅

Calling `activate_profile()` writes the current PID to `metadata.json` and the `.lock` file so that `close_profile()` can find and gracefully shut down the browser later. It also enforces the headless rule for multi-profile scenarios.

```python
pm.activate_profile(
    platform=Platform.WHATSAPP,
    profile_id="MarketingBot",
    browser_obj=browser,
)
```

---

## Step 6: Enable Encryption (Optional) 🔐

To encrypt all stored messages with AES-256-GCM, call `enable_encryption()` once. The returned key is passed to `MessageProcessor` later.

```python
# First-time setup
key = pm.enable_encryption(Platform.WHATSAPP, "MarketingBot")

# On subsequent runs — reload the saved key
# key = pm.get_key(Platform.WHATSAPP, "MarketingBot")
```

---

## Graceful Shutdown 🛑

```python
async def shutdown():
    await pm.close_profile(Platform.WHATSAPP, "MarketingBot")
    print("Profile closed and session saved.")

asyncio.run(shutdown())
```

---

## Key Takeaways 💡

| Concept | Why It Matters |
|---------|---------------|
| **Profile isolation** | Each `profile_id` is a completely separate virtual browser user — no shared state. |
| **Fingerprint persistence** | `fingerprint.pkl` ensures the same browser identity across restarts — critical for WhatsApp session continuity. |
| **Idempotent creation** | `create_profile()` is safe to call at every script startup. |
| **Multi-profile headless** | `activate_profile()` auto-enforces headless for the 2nd+ profile — no manual configuration needed. |
| **Encrypted storage** | One call to `enable_encryption()` activates AES-256-GCM on all future messages for that profile. |

For advanced profile operations (listing, deletion, encryption), see [ProfileManager](./ProfileManager.md).  
For fingerprint internals, see [BrowserForgeCompatible](./BrowserForgeCompatible.md).
