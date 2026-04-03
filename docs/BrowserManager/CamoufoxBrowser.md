# 🦊 CamoufoxBrowser

`camouchat.BrowserManager.camoufox_browser`

`CamoufoxBrowser` is the async browser lifecycle manager at the core of the SDK. It wraps **Camoufox** (an anti-detect, patched Firefox) and ties it to a `ProfileInfo`-isolated user-data directory and a `BrowserForgeCompatible`-generated fingerprint. Every instance is bound to exactly one profile, giving you full session isolation between bots.

---

## 🏗️ Class Overview

```python
class CamoufoxBrowser(BrowserInterface):
    Map: Dict[int, BrowserContext] = {}  # Process-wide PID → BrowserContext registry
```

The class-level `Map` dictionary tracks all active browser contexts keyed by OS process ID. This is what enables `ProfileManager` to locate and gracefully shut down a specific browser when `close_profile()` is called.

---

## 🛠️ Constructor

```python
CamoufoxBrowser(
    config: BrowserConfig,
    profile: ProfileInfo,
    log: Optional[Union[Logger, LoggerAdapter]] = None,
)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config` | `BrowserConfig` | ✅ Yes | Full browser configuration (locale, headless, fingerprint, etc.). |
| `profile` | `ProfileInfo` | ✅ Yes | The sandboxed profile this browser instance belongs to. |
| `log` | `Logger \| LoggerAdapter` | ❌ No | Logger instance. Defaults to `camouchatLogger` if omitted. |

> [!IMPORTANT]
> The constructor validates three things immediately and raises `BrowserException` if any fail:
> 1. `config.fingerprint_obj` must not be `None` — a fingerprint generator is required.
> 2. `profile.cache_dir` must exist — this is where Camoufox stores its persistent session.
> 3. `profile.fingerprint_path` must be resolved — used to load/save the fingerprint pickle.

```python
from camouchat.BrowserManager import (
    CamoufoxBrowser, BrowserConfig, BrowserForge,
    ProfileManager, Platform
)
from camouchat.camouchat_logger import camouchatLogger

pm = ProfileManager()
profile = pm.create_profile(Platform.WHATSAPP, "WorkBot")

bf = BrowserForge()

config = BrowserConfig(
    platform=Platform.WHATSAPP,
    locale="en-US",
    headless=False,  # False = visible browser window
    enable_cache=True,  # True = reuse DOM cache (good for debugging)
    fingerprint_obj=bf,  # The BrowserForgeCompatible instance — NOT the generated Fingerprint
    prefs={},  # Pass {} to avoid suspicious Firefox prefs
    addons=[],  # Absolute paths to .xpi/.zip extension files
)

browser = CamoufoxBrowser(config=config, profile=profile, log=camouchatLogger)
```

> [!NOTE]
> `fingerprint_obj` in `BrowserConfig` should be your **`BrowserForgeCompatible` instance**, not the raw `Fingerprint` object. The browser calls `bf.get_fg(profile=self.profile)` internally at launch time, so it always loads the correct persisted fingerprint for that profile.

---

## 📦 Methods

### `get_instance() → BrowserContext`

Launches the Camoufox browser if it has not been started yet, and returns the `BrowserContext`. On first call, it registers the context in `CamoufoxBrowser.Map` using the OS PID as the key and syncs `profile.last_active_pid` for recovery.

```python
context: BrowserContext = await browser.get_instance()
```

Subsequent calls return the already-running context immediately without re-launching.

---

### `get_page() → Page`

The most-used method. Returns a Playwright `Page` object ready for navigation.

- **Smart reuse**: If there is already a blank `about:blank` page open in the context, it returns that instead of creating a new one. This avoids unnecessary tab proliferation.
- **Auto-launch**: If the browser has not been started yet, it calls `get_instance()` first.

```python
page = await browser.get_page()
await page.goto("https://web.whatsapp.com")
```

---

### `close_browser_by_pid(pid: int) → bool` *(classmethod)*

Gracefully shuts down the browser associated with a given OS PID and removes it from the class-level `Map`.

```python
success = await CamoufoxBrowser.close_browser_by_pid(os.getpid())
```

This is called internally by `ProfileManager.close_profile()`. You typically don't need to call it directly.

---

## ⚙️ Internal: `__GetBrowser__(tries=1)` *(private)*

The actual Camoufox launch logic. It:
1. Calls `BrowserForgeCompatible.get_fg(profile)` to get a per-profile `Fingerprint`.
2. Passes it to `AsyncCamoufox` with `geoip=True`, `humanize=True`, and `persistent_context=True` pointing at `profile.cache_dir`.
3. On `InvalidIP`, retries up to 5 times — useful for VPN-adjacent environments where the IP may be flagged temporarily.

> [!TIP]
> `persistent_context=True` is what gives you session continuity. You only need to log in once; subsequent launches reuse the saved session from `profile.cache_dir`.

---

## ⚙️ BrowserConfig Reference

`browser_config.py` — `BrowserConfig` is a dataclass with a `from_dict()` factory.

| Field | Type | Default | Why It Exists |
|-------|------|---------|---------------|
| `platform` | `Platform` | (required) | Tags the config with the target platform. Passed to multi-profile logic and future platform-routing. |
| `locale` | `str` | `"en-US"` | Sent as the `Accept-Language` header / browser locale. Match your region to avoid geo-detection. |
| `headless` | `bool` | `False` | `False` = invisible browser. When `ProfileManager.activate_profile()` detects more than 1 active profile, it forcibly sets this to `True` for the new browser to conserve display resources. |
| `enable_cache` | `bool` | `False` | Enables Camoufox's internal DOM cache. Useful during debugging (`True`). Keep `False` in production to save RAM and prevent stale-DOM issues. |
| `geoip` | `bool` | `True` | **Spoofs geolocation** (coords, timezone, country) based on IP. Recommended with proxies. |
| `proxy` | `dict` | `None` | Proxy config (server, username, password). **Residential proxies** are strongly recommended. |
| `fingerprint_obj` | `BrowserForgeCapable` | (required) | The fingerprint generator. Must not be `None`; the browser calls `get_fg()` on it at launch. |
| `prefs` | `dict` | `{}` | Raw Firefox `user.js` preferences. Pass `{}` in stealth mode — custom prefs can betray automation. |
| `addons` | `list[str]` | `[]` | Absolute local paths to browser extension `.zip`/`.xpi` files to load on startup. |

```python
# Factory from dict (handy for config files)
config = BrowserConfig.from_dict({
    "platform": Platform.WHATSAPP,
    "locale": "en-IN",
    "headless": False,
    "geoip": True,
    "proxy": {
        "server": "http://your-residential-proxy.com:8080",
        "username": "your_user",
        "password": "your_password"
    },
    "enable_cache": False,
    "fingerprint_obj": BrowserForgeCompatible(),
})
```

---

## 🛡️ Why Camoufox?

- **Fingerprint Spoofing**: Every HTTP/JS attribute that fingerprinting scripts interrogate (user-agent, platform, screen, fonts, WebGL, Canvas, AudioContext, etc.) is consistently spoofed to match the generated `Fingerprint` object.
- **GeoIP Awareness**: `geoip=True` makes the browser advertise a geolocation (coordinates, timezone, language) that matches your IP address — eliminating a common fingerprinting signal mismatch. This also spoofs the WebRTC IP address.
- **Proxy Support**: Full integration for proxies with residential proxy recommendations to ensure the highest levels of stealth and session reliability.
- **Humanization**: `humanize=True` enables Camoufox's built-in mouse trajectory randomization and jitter, layered on top of the SDK's own `HumanInteractionController`.
- **Session Persistence**: Cookies, local storage, and service workers are preserved between runs in `profile.cache_dir`.

---

## 💡 Pro Tips

- **Multiple bots on one machine**: `ProfileManager.activate_profile()` automatically sets `headless=True` for the second+ browser so your display server is not overwhelmed.
- **Don't share `BrowserForgeCompatible` instances** across profiles — each profile maintains its own `fingerprint.pkl` file, and `get_fg()` reads/writes it based on `profile.fingerprint_path`.
- **PID tracking**: After `get_instance()`, the current PID is written to `profile.last_active_pid` *in memory* (not on disk). `ProfileManager.activate_profile()` writes it to `metadata.json`. This separation prevents partial-write corruption if the process crashes mid-launch.
