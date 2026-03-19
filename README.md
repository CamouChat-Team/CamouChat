<table>
<tr>
<td style="vertical-align: middle; padding-right: 1px; padding-left: 1px;">
  <img src="assets/camouchat.png" width="250" alt="CamouChat Logo"/>
</td>
<td style="vertical-align: middle;">
<pre style="margin:0;">
   ____                                  ____ _           _   
  / ___| __ _ _ __ ___   ___  _   _     / ___| |__   __ _| |_ 
 | |    / _` | '_ ` _ \ / _ \| | | |   | |   | '_ \ / _` | __|
 | |___| (_| | | | | | | (_) | |_| |   | |___| | | | (_| | |_ 
  \____|\__,_|_| |_| |_|\___/ \__,_|    \____|_| |_|\__,_|\__|
</pre>
</td>
</tr>
</table>

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/tweakio-sdk?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/tweakio-sdk)
[![PyPI - Version](https://img.shields.io/pypi/v/tweakio-sdk?label=tweakio-sdk)](https://pypi.org/project/tweakio-sdk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tweakio-sdk)](https://pypi.org/project/tweakio-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-%3E90%25-brightgreen)](https://github.com/BITS-Rohit/tweakio-sdk)

---

## Why CamouChat?

Before building CamouChat, several existing libraries were evaluated to understand current limitations.

WhatsApp libs analysis : [[**docs**]](docs/Platforms/Analysis/whatsapp_libs.md)

### Problem Summary

Across existing tools, common limitations were observed:

- Fragile selector-based automation  
- Lack of multi-account/profile isolation  
- Weak or absent anti-detection strategies  
- Poor long-term maintenance in many projects  
- No unified architecture across platforms  

---

## Introducing CamouChat

CamouChat is designed as a **developer-focused SDK**, not just another wrapper.

It prioritizes:

- **Reliability over shortcuts**  
- **Stealth-aware automation**  
- **Controlled and extensible architecture**  

Instead of competing on raw API speed, CamouChat focuses on building a **stable and maintainable automation layer**.

---

## Key Benefits --------------------------

1. **Anti-Detection Browser Layer**  
   Built on [[**Camoufox**]](https://github.com/daijro/camoufox), a patched Playwright-based Firefox with stealth-oriented capabilities.

2. **Dynamic Fingerprinting**  
   Uses [[**BrowserForge**]](https://github.com/daijro/browserforge) for realistic and adaptive fingerprint generation.

3. **Multi-Profile Management**  
   Run multiple isolated accounts with proper session separation and lifecycle control.

4. **Secure Message Storage**  
   AES-GCM-256 encryption ensures internal data protection.

5. **Database Flexibility & Safety**  
   Powered by [[**SQLAlchemy**]](https://github.com/sqlalchemy/sqlalchemy):
   - Supports multiple databases  
   - Uses parameterized queries to reduce injection risks  

6. **Browser Sandboxing**  
   Each profile operates in isolation to prevent fingerprint leakage.

7. **Reliable Session Handling**  
   Built on Playwright’s robust session persistence mechanisms.

8. **Extensible Architecture**  
   Designed to support multiple messaging platforms under a unified SDK.

9. **Best-of Approach**  
   Incorporates stable techniques from existing tools while addressing their limitations.

10. **Rate Limiting Support**  
   Helps build safer automation workflows and reduce detection risks.

11. **Humanized Interaction Layer**  
   Simulates realistic typing and mouse behavior to reduce automation patterns.

12. **Local-First Privacy**  
   - No external data transmission  
   - No hidden telemetry  
   - All data remains on the user’s system  

13. **Cross-Platform Support**  
   Works consistently across:
   - Linux  
   - macOS  
   - Windows  

---

## Philosophy

CamouChat is built with a clear direction:

> Provide a **unified, reliable, and automation-focused SDK**  
> so developers don’t need to relearn tools for every platform.

>> **CamouChat focuses on reducing detection signals,**  
>> **not bypassing platform safeguards.**

---


##  --------------------------  Installation -------------------------- 

> [!IMPORTANT]
> **CamouChat** is currently in active development and **not yet published on PyPI**. To use or contribute to the SDK, please follow the [Contributor's Flow](#-contributors-flow-development-setup) below to install from source.

### Using `uv` (Recommended)

```bash
# Create & activate virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package with required browser support
uv pip install camouchat "camoufox[geoip]"

# Download Camoufox browser binaries
python -m camoufox fetch
```

**Using `pip`**:
```bash
# Create & activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install package with required browser support
pip install camouchat "camoufox[geoip]"

# Download Camoufox browser binaries
python -m camoufox fetch
```

> Camoufox uses a custom patched Firefox browser.
> Run `python -m camoufox fetch` to download required binaries.
> No need to run `playwright install`.

---

## --------------------------  Quick Start -------------------------- 

👉 **Quick Start Guides**: [[**docs**]](https://github.com/BITS-Rohit/tweakio-sdk/tree/main/docs)

Whether you need basic chat fetching, multi-profile anti-detect sessions, or advanced async encrypted storage, you will find clean examples in the specific module guides.

---

## 🛠 Contributor's Flow (Development Setup)

Since the package is not yet on PyPI, follow these steps to set up a local development environment.

### 1. Fork & Clone
First, [fork the repository](https://github.com/BITS-Rohit/tweakio-sdk/fork) on GitHub, then clone it locally:

```bash
git clone https://github.com/YOUR_USERNAME/tweakio-sdk.git
cd tweakio-sdk
```

### 2. Dependency Management (using `uv`)
We use [**uv**](https://github.com/astral-sh/uv) for lightning-fast dependency management and virtual environments.

```bash
# Install all dependencies and create .venv
uv sync

# Activate the environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Download required browser binaries
python -m camoufox fetch
```

### 3. Verify Installation
Run the test suite to ensure everything is configured correctly:

```bash
uv run pytest
```

### 4. Contributing
- Create a feature branch: `git checkout -b feat/amazing-feature`
- Commit your changes: `git commit -m "feat: add amazing feature"`
- Push to your fork: `git push origin feat/amazing-feature`
- Open a Pull Request!

---

### 🗺 Roadmap ---------------------------------------------------- 
Currently on [[**v0.6**]](docs/Series/v_0_6x.md)
### v0.6 — Core Infrastructure : [[docs]](docs/Series/v_0_6x.md)


### v0.7 — WebSelector Stability Techniques 
- [ ] Cherry Picked stable Selector Techniques 
- [ ] WhatsApp Stability Increase
- [ ] Tests >=80% & Lint Checking Updated.

### v0.8
- [ ] Saving Media from WhatsApp to local Feature
- [ ] WebUI Hardening
- [ ] Tests >=85% & Lint Checking updated.

### v0.9
- [ ] Extra WhatsApp Functions 
- [ ] Internal Stability Focused

### v1.0 forward — arattai (Coming Soon)
- [ ] arattai Platform Next Integration

---

### -------------------------- FAQ -------------------------- 

**Q: Will I get banned?**  
A: It is rare but can happen on the least. Some preventions is that always use rate limiter given by the sdk. Dont spam. It uses Patched Browser so even if have to be done something it will be a soft ban [Soft ban : Browser gets logged out Not direct number ban : Tested with real numbers.]. Still if u have a spare account use that first for 100% safe.

**Q: Can I use this for spam?**  
A: No. This SDK is for legitimate automation for devs | agents | Small Business Model Testing .Doing spam may risk ur number , Try at ur own risk.

**Q: Why not just use the WhatsApp Business API?**  
A: Business API has message template restrictions and approval processes. Cost for every freaking message . You would need to verify urself first. 
Also limited behavior.We automate the web itself. **-- Free and Open Source**

---

### --------------------------  License -------------------------- 

MIT License — see [[**LICENSE**]](LICENSE)

---

## ⚠ Security & Usage Guidelines -------------------------- 

CamouChat is intended for **educational, research, and controlled automation use cases**.  
By using this SDK, you agree to use it responsibly and in compliance with applicable laws and platform policies.

---

### Acceptable Usage

- Academic research and benchmarking  
- Personal automation and developer tooling  
- Prototyping agents and automation workflows  
- Learning browser automation and system design  

---

### Prohibited Usage

- Violating platform Terms of Service (ToS)  
- Sending spam, bulk, or unsolicited messages  
- Attempting to bypass platform safeguards or protections  
- Operating automation at scale without proper compliance  
- Any activity that may harm users, services, or infrastructure  

---

### Security Best Practices

- Use **dedicated or test accounts** for automation (avoid personal accounts)  
- Respect platform limits and avoid high-frequency actions  
- Maintain realistic interaction patterns (avoid unnatural behavior)  
- Secure credentials, session data, and local storage  
- Monitor accounts regularly for warnings or unusual activity  

---

### Data & Privacy

- CamouChat follows a **local-first approach**  
- No data is transmitted externally by the SDK  
- All sessions, logs, and data remain on the user’s system  
- Users are responsible for securing their environment and data  

---

### Responsibility Disclaimer

- CamouChat provides development tooling, not guarantees of anonymity or bypass  
- It does **not ensure protection against platform detection mechanisms**  
- The maintainers are **not responsible** for misuse or resulting consequences  
- Users must ensure compliance with:
  - Platform policies  
  - Local laws and regulations  

---

### Ethical Use 

> CamouChat is designed to assist development and automation workflows.  
> It should not be used to exploit, abuse, or disrupt platforms or users.

---

## 💖 Thanks to all our Contributors!

---

_Built with ❤️ by BITS-Rohit and the [**CamouChat**](https://github.com/BITS-Rohit/tweakio-sdk) community_