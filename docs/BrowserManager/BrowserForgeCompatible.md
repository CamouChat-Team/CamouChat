# 🧬 BrowserForgeCompatible

`camouchat.BrowserManager.browserforge_manager`

`BrowserForgeCompatible` is the fingerprint manager for CamouChat. It generates and persists browser fingerprints using the **BrowserForge** library, ensuring the spoofed screen dimensions match your machine's actual display. This prevents the most common fingerprinting signal mismatch — a browser reporting a screen size that doesn't match what's physically present.

---

## 🛠️ Constructor

```python
BrowserForgeCompatible(log: Optional[Union[Logger, LoggerAdapter]] = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log` | `Logger \| LoggerAdapter` | `camouchatLogger` | Logger for fingerprint generation events and warning logs. |

```python
from camouchat.BrowserManager import BrowserForge
from camouchat.camouchat_logger import camouchatLogger

bf = BrowserForge(log=camouchatLogger)
```

---

## 📦 Methods

### `get_fg(profile) → Fingerprint`

Loads an existing fingerprint from the profile's `fingerprint.pkl` file, or generates a new one if the file is empty. The fingerprint is always persisted to disk for future runs.

| Parameter | Type | Description |
|-----------|------|-------------|
| `profile` | `ProfileInfo` | The profile whose `fingerprint_path` (`fingerprint.pkl`) is used for load/save. |

```python
fg = bf.get_fg(profile=profile)
# Returns a browserforge.fingerprints.Fingerprint object
```

**Decision logic**:
- If `fingerprint.pkl` **exists and is non-empty** → loads and returns the saved fingerprint. No generation needed. This maintains a consistent browser identity across restarts.
- If `fingerprint.pkl` **exists but is empty** (just created by `ProfileManager.create_profile()`) → calls `__gen_fg__()` to generate a screen-matched fingerprint, saves it, and returns it.
- If the path **doesn't exist at all** → raises `BrowserException("path given does not exist")`.

> [!NOTE]
> `get_fg()` is called automatically by `CamoufoxBrowser.__GetBrowser__()` at browser launch time. You only need to call it manually if you want to inspect the fingerprint before launching.

---

### `get_fingerprint_as_dict(profile) → dict` *(static)*

Loads the fingerprint file and deserializes it as JSON (for fingerprints stored in JSON format, not pickle). Validates that the file exists, is non-empty, and contains a valid dict.

```python
fg_dict = BrowserForgeCompatible.get_fingerprint_as_dict(profile=profile)
print(fg_dict.get("userAgent"))
```

> [!NOTE]
> This static method is primarily used for debugging or inspection — the active fingerprint used by Camoufox is always the pickle-based one loaded by `get_fg()`.

---

### `get_screen_size() → Tuple[int, int]` *(static)*

Returns the width and height of the primary display in pixels. Used internally by `__gen_fg__()` to filter fingerprints to screen-matching candidates.

Platform support:
- **Windows**: `ctypes.windll.user32.GetSystemMetrics()` with DPI awareness.
- **Linux (X11)**: `xdpyinfo` subprocess — needs X11 running.
- **macOS**: `Quartz.CGDisplayPixelsWide/High()`.

```python
w, h = BrowserForgeCompatible.get_screen_size()
print(f"Your screen: {w}x{h}")
```

Raises `BrowserException` if screen detection fails or the OS is unsupported.

---

## ⚙️ Internal: `__gen_fg__()` — Screen-Matched Generation

This private method loops through `FingerprintGenerator().generate()` until the generated fingerprint's screen dimensions are within **10% tolerance** of the actual display:

```python
# Tolerance check (±10% on both width and height)
if abs(w - real_w) / real_w < 0.1 and abs(h - real_h) / real_h < 0.1:
    return fg  # Accept this fingerprint
```

- Maximum **10 attempts** before giving up and returning the best available result.
- Each regeneration attempt is logged as a `WARNING` so you can see how many tries were needed.

> [!TIP]
> On machines with unusual resolutions (ultra-wide, HiDPI, virtual display), you may see several "regenerating" warnings. This is normal — BrowserForge's fingerprint database may not have an exact match, and the 10-attempt cap ensures the bot doesn't loop forever.

---

## 💡 Why Fingerprint Screen-Matching Matters

Browser fingerprinting services check whether the viewport size reported by the browser matches the `screen.width`/`screen.height` properties exposed to JavaScript. A mismatch (e.g., a 1920×1080 browser claiming screen size 2560×1440) is a strong bot signal.

By generating fingerprints whose screen dimensions are within ±10% of your physical display, CamouChat ensures this consistency check passes — even in headless mode where the real display is not directly accessible.

---

## 💡 Pro Tips

- **Don't call `get_fg()` before the profile directory is set up**: `ProfileManager.create_profile()` creates the empty `fingerprint.pkl` file. Calling `get_fg()` before `create_profile()` will raise `BrowserException`.
- **One `BrowserForgeCompatible` instance per application is fine**: The class is stateless. You can share one instance across multiple profiles — it reads/writes each profile's own `fingerprint.pkl` independently via the `profile` parameter.
- **Fingerprint stability**: Once generated, the fingerprint is locked to the profile. WhatsApp (and any fingerprinting service) will see the same browser attributes every time. Deleting `fingerprint.pkl` forces a new fingerprint on the next run — treat this as "generating a new browser identity."
