# 🦊 CamoufoxBrowser: Your stealthy window to the web

The `CamoufoxBrowser` is the heart of the SDK's browser interaction. It’s built on top of **Camoufox** (a modified Firefox) to provide elite-level fingerprinting and anti-detection capabilities. 

When you use `CamoufoxBrowser`, you're not just opening a browser; you're opening a **stealthy, sandboxed environment** that looks like a real human user.

---

### 🛠️ Setting up the Browser

To start the browser, you need three things: a `BrowserConfig`, a `ProfileInfo`, and a `Logger`.

```python
from camouchat.BrowserManager import CamoufoxBrowser, BrowserConfig, Platform

# 1. Setup the Config
config = BrowserConfig(
    platform=Platform.WHATSAPP,
    # ------------- This is a Required Parameter -------------

    locale="en-Us",
    # Or your side in case your Locale is different.

    enable_cache=False,
    # Generally not needed as True. To save RAM & resources usage, make it False.

    headless=True,
    # Only use True if you want to see Browser working as visible UI.
    # Note: If multiple profiles are active, this will automatically set to False for others.

    fingerprint_obj=BrowserForgeCompatible().get_fg(profile=work_profile)
    # ------------- This is a Required Parameter -------------
    # This automatically uses the path in the ProfileInfo dataclass.
)

# 2. Get your Profile
profile = pm_obj.get_profile(Platform.WHATSAPP, "MyBot")

# 3. Create the Browser
browser = CamoufoxBrowser(config=config, profile=profile, log=my_logger)
```

---

### 📦 Key Functions

#### 1. `get_instance()`
This method launches the browser (if it's not already running) and returns the Playwright `BrowserContext`.
- **Note**: It automatically handles fingerprints and IP retries for you!
```python
context = await browser.get_instance()
```

---

#### 2. `get_page()`
This is the method you'll use most often. It returns a `Page` object that you can use to navigate websites.
- **Smart Logic**: If there's already a blank page open, it reuses it. Otherwise, it opens a fresh one.
```python
page = await browser.get_page()
await page.goto("https://web.whatsapp.com")
```

---

### ⚙️ BrowserConfig: Fine-tuning your Stealth

The `BrowserConfig` class lets you customize how your browser behaves:

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `platform` | `Platform` | **Required.** Platform class for to give platform attribute anywhere. |
| `locale` | `str` | System locale (e.g., `"en-Us"`). Use this if your locale is different. |
| `headless` | `bool` | **True** for visible UI. If multiple profiles are active, this is automatically set to False for others. |
| `enable_cache` | `bool` | **False** recommended to save RAM & resource usage. |
| `prefs` | `dict` | Experimental. Recommened passed as empty dict `{}` for stealth. |
| `addons` | `list` | List of real zip download paths for Extensions/Addons. |

---

### 🛡️ Why Camoufox?
*   **Anti-Detection**: Built-in protection against bot-detection scripts used by major sites.
*   **Humanization**: Automatically moves the mouse and types in a way that looks human.
*   **Auto-Cleanup**: When you close the browser, it syncs its state back to the profile automatically.

---

### 💡 Pro Tip
If you are running multiple bots on the same machine, any additional browsers will automatically have their visibility set to **False** to save your computer's RAM and keep things stable! 🚀
