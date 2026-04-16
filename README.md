<div align="center">
  <h1>⚠️ tweakio-sdk — DEPRECATED</h1>
  <p><b>This package has been rebranded. Please migrate to CamouChat.</b></p>
</div>

<p align="center">
  <a href="https://pypi.org/project/camouchat-whatsapp/">
      <img src="https://img.shields.io/badge/Migrate%20To-camouchat--whatsapp-orange?style=for-the-badge" />
  </a>
  <a href="https://pypi.org/project/camouchat/">
      <img src="https://img.shields.io/badge/Umbrella-camouchat-blue?style=for-the-badge" />
  </a>
  <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  </a>
</p>

---

> [!CAUTION]
> **`tweakio-sdk` is officially deprecated and will no longer receive updates.**
> This package has been fully rebranded and evolved into the **CamouChat Plugin Ecosystem**.
>
> **Please migrate immediately:**
>
> | Old | New |
> |---|---|
> | `pip install tweakio-sdk` | `pip install camouchat-whatsapp` |
>
> Full documentation, changelogs, and API references are available at the new locations listed below.

---

## 📦 New Package Locations

| Package | Role | PyPI |
|---|---|---|
| [`camouchat`](https://pypi.org/project/camouchat/) | Umbrella entry point (installs all plugins) | [![PyPI](https://img.shields.io/pypi/v/camouchat?color=blue)](https://pypi.org/project/camouchat/) |
| [`camouchat-core`](https://pypi.org/project/camouchat-core/) | Core SDK — protocols, logging, encrypted storage | [![PyPI](https://img.shields.io/pypi/v/camouchat-core?color=blue)](https://pypi.org/project/camouchat-core/) |
| [`camouchat-browser`](https://pypi.org/project/camouchat-browser/) | Stealth browser engine (Camoufox + BrowserForge) | [![PyPI](https://img.shields.io/pypi/v/camouchat-browser?color=blue)](https://pypi.org/project/camouchat-browser/) |
| [`camouchat-whatsapp`](https://pypi.org/project/camouchat-whatsapp/) | WhatsApp automation plugin (wa-js, multi-account) | [![PyPI](https://img.shields.io/pypi/v/camouchat-whatsapp?color=blue)](https://pypi.org/project/camouchat-whatsapp/) |

## 📚 Documentation

* 🏠 **Ecosystem Hub**: [github.com/CamouChat-Team/CamouChat](https://github.com/CamouChat-Team/CamouChat)
* 📖 **Core Architecture**: [camouchat-core/docs](https://github.com/CamouChat-Team/camouchat-core/tree/main/docs)
* 📖 **Browser Configuration**: [camouchat-browser/docs](https://github.com/CamouChat-Team/camouchat-browser/tree/main/docs)
* 📖 **WhatsApp API & Models**: [camouchat-whatsapp/docs](https://github.com/CamouChat-Team/camouchat-whatsapp/tree/main/docs)

---

## Historical README (v0.6.1)

> The content below is the original tweakio-sdk / CamouChat v0.6 README, preserved for reference only.

---

---

## Introduction to CamouChat

CamouChat is an advanced, strictly decoupled ecosystem designed for researchers and developers to build high-performance Web Automation agents safely. Initially built for highly secured chat applications like WhatsApp, it utilizes **Camoufox** to achieve industry-leading anti-detection capabilities.

It provides a standardized framework incorporating **end-to-end encrypted local storage**, **isolated sandbox profiling**, and **humanized interaction schemas** — completely removing the fragility associated with raw DOM scraping or unsecured automation libraries.

This repository serves as the central hub and entry point for the entire CamouChat plugin ecosystem.

> [!IMPORTANT]
> **v0.7.0 Update** — CamouChat is now a decoupled plugin ecosystem. The `camouchat` package on PyPI is the umbrella entry point. WhatsApp automation lives in **[`camouchat-whatsapp`](https://pypi.org/project/camouchat-whatsapp/)** — install that for full functionality. Existing users of the old monolithic `camouchat` package: no API changes, just point your install to `camouchat-whatsapp` going forward.

---

## Why CamouChat?

Before building CamouChat, maintaining reliable web automation pipelines across restricted platforms presented major challenges:

* **Fragile Automation**: Hardcoded CSS selectors break constantly on platform UI updates. 
* **Bot Identification**: Basic Puppeteer/Playwright instances trigger modern captchas and integrity scanners immediately.
* **Account Risk**: Lack of isolated cookie/cache containment leads to swift cross-account detection and IP shadowbans.
* **Architecture Bloat**: Existing libraries are typically monolithic, tightly coupled wrappers that force you into a single way of handling tasks.

**CamouChat solves this by establishing a protocol-driven SDK, routing actions through secure internal APIs (injecting JS bridges without triggering scanners) and standardizing storage schemas globally.**

---

## 🧩 The Plugin Ecosystem

Starting from `v0.7.0`, CamouChat has been strictly decoupled into specialized plugins. You install exactly what you need.

### 1. [camouchat-core](https://github.com/CamouChat-Team/camouchat-core) — The Foundation &nbsp; [![PyPI](https://img.shields.io/pypi/v/camouchat-core?color=blue)](https://pypi.org/project/camouchat-core/)
The required central SDK interface. Provides the foundational structures:
- Standardized `typing.Protocol` contracts for interoperability.
- Asynchronous Logging Engine (`concurrent-log-handler`).
- Strict AES-GCM-256 Storage & Metadata interfaces.

### 2. [camouchat-browser](https://github.com/CamouChat-Team/camouchat-browser) — The Engine &nbsp; [![PyPI](https://img.shields.io/pypi/v/camouchat-browser?color=blue)](https://pypi.org/project/camouchat-browser/)
The stealth browser layer built for Web interactions.
- Embeds [Camoufox](https://camoufox.com/) for deep connection and JS fingerprint spoofing.
- Generates dynamic hardware profiles via `browserforge`.
- Automated OS-aware profile sandboxing and encryption.

### 3. [camouchat-whatsapp](https://github.com/CamouChat-Team/camouchat-whatsapp) — The Implementation &nbsp; [![PyPI](https://img.shields.io/pypi/v/camouchat-whatsapp?color=blue)](https://pypi.org/project/camouchat-whatsapp/)
A platform-specific plugin leveraging the Core and Browser ecosystems to automate WhatsApp Web perfectly.
- Complete internal API bridge using [wa-js](https://github.com/wppconnect-team/wa-js) natively.
- Zero DOM Scraping — Event-driven interaction.
- Support for complex media fetching, stealth timing, and fully-typed async architectures.

---

## 🚀 Quick Install

> 📦 **Full WhatsApp plugin → [`camouchat-whatsapp` on PyPI](https://pypi.org/project/camouchat-whatsapp/)** — detailed docs, changelog, and API reference live there.

To build a full, automated WhatsApp agent utilizing the Camoufox engine, install the ecosystem via `uv` or `pip`:

### Using `uv` (Recommended)
```bash
uv add camouchat-whatsapp "camoufox[geoip]"
uv run python -m camoufox fetch
```

### Using `pip`
```bash
pip install camouchat-whatsapp "camoufox[geoip]"
python -m camoufox fetch
```

> [!WARNING]
> Running `camoufox fetch` is a **mandatory** one-time step that downloads the compiled Firefox binaries. Normal package managers cannot perform this hook automatically.

---

## 📚 Global Documentation

* 📖 **Core Architecture**: [Link](https://github.com/CamouChat-Team/camouchat-core/tree/main/docs)
* 📖 **Browser Configurations**: [Link](https://github.com/CamouChat-Team/camouchat-browser/tree/main/docs)
* 📖 **WhatsApp API & Models**: [Link](https://github.com/CamouChat-Team/camouchat-whatsapp/tree/main/docs)

---

## ⚖️ Security & Ethics

CamouChat provides powerful browser automation and stealth infrastructure. With this power comes the responsibility to use it ethically and in compliance with the rules of the platforms you interact with. 

Please read our mandatory **[Security & Ethics Guidelines](https://github.com/CamouChat-Team/CamouChat/blob/main/SECURITY.md)** regarding acceptable use, anti-spam policies, and anti-detection disclaimers before utilizing the ecosystem.

---

## 🤝 Community & Support

* [Code of Conduct](https://github.com/CamouChat-Team/camouchat-core/blob/main/CODE_OF_CONDUCT.md)
* [Changelog / Release Notes](https://github.com/CamouChat-Team/camouchat-core/releases)
* Submitting issues: Please file platform-specific issues directly in the corresponding plugin repository (`camouchat-whatsapp`, etc.).

---

<p align="center">
  Built with ❤️ by BITS-Rohit and the CamouChat community
</p>
