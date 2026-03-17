# BrowserManager QuickStart Guide 🚀

The `BrowserManager` module is the foundation of **CamouChat**. It handles sandboxed profile creation, fingerprinting, and browser lifecycle management.

Follow these steps to set up your isolated environment.

---

### Step 1: Initialize the ProfileManager 🗃️

The `ProfileManager` manages all your virtual browser identities on your disk.

```python
from camouchat.BrowserManager import ProfileManager, Platform

# Get a Object of ProfileManager
pm = ProfileManager()

# Create a Profile with a name u want to add for your profile
profile = pm.create_profile(
    platform=Platform.WHATSAPP,
    # ------------- This is a Required parameter -------------
    # or Any Platform available in the Platform class
    profile_id="MarketingBot",
    # ------------- This is a Required parameter -------------
    # This is your profile name for that platform.
)

print(f"✅ Profile created at: {profile.profile_dir}")
```

> [!TIP]
> Each profile gets its own unique fingerprint and cache directory, making them appear as completely different users/devices to websites.

---

### Step 2: Configure your Stealth Browser 🕵️‍♂️

Next, we define how the browser should behave. We use `BrowserForge` to generate a fingerprint that exactly matches your real hardware specs to minimize detection.

```python
from camouchat.BrowserManager import BrowserConfig, BrowserForgeCompatible

# Initialize the fingerprint generator
bf = BrowserForgeCompatible()

# Define the configuration dictionary
config_data = {
    "platform": Platform.WHATSAPP,
    # ------------- This is Required Parameter -------------
    "locale": "en-US",           
    "headless": False,            # Only use True if u want to see Browser working as visible UI.
    "enable_cache": True,        
    "fingerprint_obj": bf.get_fg(profile=profile), 
    # ------------- This is a Required Parameter -------------
    # This Automatically uses the path in the dataclass given.
    "prefs": {},                 
    "addons": []                 
}

# Create the config object
browser_config = BrowserConfig.from_dict(config_data)
```

---

### Step 3: Launch the Camoufox Browser 🦊

Bringing it all together. The `CamoufoxBrowser` is a customized, anti-detect version of Firefox built for high-stealth automation.

```python
from camouchat.BrowserManager import CamoufoxBrowser
from camouchat.camouchat_logger import CamouChatLogger

# Initialize the browser
browser = CamoufoxBrowser(
    # It takes 3 parameter & All are REQUIRED PARAMETER:
    config=browser_config,
    # This is the browser_config we just created earlier.
    profile=profile,
    # That profile goes here so that browser is saved & Isolated.
    log=CamouChatLogger,
)


# Launch and get our active page
async def start_session():
    # This page will be used throughout the platforms.
    page = await browser.get_page()
    await page.goto("https://web.whatsapp.com")
    print("🌐 Stealth browser is live!")


import asyncio

asyncio.run(start_session())
```

---

### Key Takeaways 💡

- **Isolation**: Each `profile_id` is a separate world. `MarketingBot` won't share cookies or cache with `PersonalBot`.
- **Fingerprinting**: `BrowserForgeCompatible` ensures your browser "looks" real by spoofing hardware attributes realistically.
- **Stealth**: `CamoufoxBrowser` automatically handles geo-ip checks and internal humanization.

For advanced profile management (deletion, listing), see the [ProfileManager Documentation](./ProfileManager.md).
