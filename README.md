<div style="text-align: center;">
  <img src="assets/text.png" alt="CamouChat Text" />
</div>

<p align= "center">
  <a href="https://pypi.org/project/camouchat/">
    <img src="https://img.shields.io/pypi/v/camouchat?label=camouchat&color=green" />
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  </a>
  <a href="https://github.com/BITS-Rohit/tweakio-sdk">
    <img src="https://img.shields.io/badge/coverage-%3E75%25-brightgreen" />
  </a>
</p>

[//]: # (  <a href="https://pepy.tech/projects/tweakio-sdk">)
[//]: # (    <img src="https://static.pepy.tech/personalized-badge/tweakio-sdk?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads" />)
[//]: # (  </a>)

[//]: # (  <a href="https://pypi.org/project/tweakio-sdk/">)
[//]: # (    <img src="https://img.shields.io/pypi/pyversions/tweakio-sdk" />)
[//]: # (  </a>)



<!--
<p style="text-align: center;">
  <a href="https://github.com/BITS-Rohit/CamouChat/actions/workflows/ci.yml">
    <img src="https://github.com/BITS-Rohit/CamouChat/actions/workflows/ci.yml/badge.svg" />
  </a>
  <a href="https://github.com/BITS-Rohit/CamouChat/actions/workflows/github-code-scanning/codeql">
    <img src="https://github.com/BITS-Rohit/CamouChat/actions/workflows/github-code-scanning/codeql/badge.svg" />
  </a>
</p>
-->

---

## Why CamouChat?

Before building CamouChat, several existing libraries were evaluated.

👉 [Docs](docs/Platforms/Analysis/whatsapp_libs.md)

### Problem Summary

* Fragile selector-based automation
* No proper multi-account isolation
* Weak or no anti-detection strategies
* Poor long-term maintenance
* No unified architecture

---

## Introducing CamouChat

CamouChat is a **developer-focused SDK**, not just another wrapper.

**Core priorities:**

* Reliability over shortcuts
* Stealth-aware automation
* Extensible architecture

---

## Key Benefits

1. **Anti-Detection Browser Layer**
   Built on [Camoufox](https://github.com/daijro/camoufox)

2. **Dynamic Fingerprinting**
   Uses [BrowserForge](https://github.com/daijro/browserforge)

3. **Multi-Profile Management**

4. **Secure Message Storage**
   AES-GCM-256 encryption

5. **Database Flexibility**
   Powered by [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy)

6. **Browser Sandboxing**

7. **Reliable Session Handling**

8. **Extensible Architecture**

9. **Rate Limiting Support**

10. **Humanized Interaction Layer**

11. **Local-First Privacy**

* No telemetry
* No external transmission

1. **Cross-Platform**

* Linux
* macOS
* Windows

---

## Philosophy

> Provide a unified, reliable automation SDK

> Focus on reducing detection signals, not bypassing safeguards

---

## Installation

> 🚀 CamouChat v0.6 is officialy out on PyPI

### Using `uv` (Recommended)

```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

uv pip install camouchat "camoufox[geoip]"
python -m camoufox fetch
```

### Using `pip`

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install camouchat "camoufox[geoip]"
python -m camoufox fetch
```

---

## Quick Start

👉 [Docs](https://github.com/BITS-Rohit/CamouChat/tree/main/docs)

---

## Contributor Flow

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/CamouChat.git
cd CamouChat
```

### 2. Setup (uv)

```bash
uv sync
source .venv/bin/activate
python -m camoufox fetch
```

### 3. Verify

```bash
uv run pytest
```

### 4. Contribute

```bash
git checkout -b feat/your-feature
git commit -m "feat: your feature"
git push origin feat/your-feature
```

Open a PR.

---

## Roadmap

### v0.6 — Core Infrastructure

👉 [Docs](docs/Series/v_0_6x.md)

### v0.7

* Selector stability improvements
* WhatsApp reliability
* Tests ≥80%

### v0.8

* Media saving
* WebUI hardening
* Tests ≥85%

### v0.9

* Additional WhatsApp features
* Stability improvements

### v1.0+

* arattai integration

---

## FAQ

**Will I get banned?**
Rare but possible. Use rate limiting. Avoid spam. Soft bans (logout) are more common than number bans.

**Can I use this for spam?**
No. Use at your own risk.

**Why not WhatsApp Business API?**

* Template restrictions
* Approval process
* Costs per message
* Limited flexibility

---

## License

MIT — see [LICENSE](LICENSE)

---

## Security & Usage

### Acceptable Use

* Research
* Personal automation
* Prototyping
* Learning

### Prohibited Use

* ToS violations
* Spam
* Safeguard bypass attempts
* Harmful automation

### Best Practices

* Use test accounts
* Respect limits
* Avoid unnatural behavior
* Secure credentials

### Data & Privacy

* Local-first
* No external transmission

### Disclaimer

* No guarantee of undetectability
* Not responsible for misuse

---

## Thanks to all the Contributors

<!-- readme: contributors -start -->
<table>
	<tbody>
		<tr>
            <td align="center">
                <a href="https://github.com/BITS-Rohit">
                    <img src="https://avatars.githubusercontent.com/u/125949183?v=4" width="60;" alt="BITS-Rohit"/>
                    <br />
                    <sub><b>Ivy </b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/xinss-plus">
                    <img src="https://avatars.githubusercontent.com/u/260048405?v=4" width="60;" alt="xinss-plus"/>
                    <br />
                    <sub><b>Xinss</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/Adez017">
                    <img src="https://avatars.githubusercontent.com/u/142787780?v=4" width="60;" alt="Adez017"/>
                    <br />
                    <sub><b>aditya singh rathore</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/AnkithaMadhyastha">
                    <img src="https://avatars.githubusercontent.com/u/174180608?v=4" width="60;" alt="AnkithaMadhyastha"/>
                    <br />
                    <sub><b>AnkithaMadhyastha</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/dharapandya85">
                    <img src="https://avatars.githubusercontent.com/u/109461918?v=4" width="60;" alt="dharapandya85"/>
                    <br />
                    <sub><b>Dhara Pandya </b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/Vaishnav-Sabari-Girish">
                    <img src="https://avatars.githubusercontent.com/u/88036970?v=4" width="60;" alt="Vaishnav-Sabari-Girish"/>
                    <br />
                    <sub><b>Vaishnav-sabari-girish</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/OVERDOZZZE">
                    <img src="https://avatars.githubusercontent.com/u/113797353?v=4" width="60;" alt="OVERDOZZZE"/>
                    <br />
                    <sub><b>Saparbekov Nurdan</b></sub>
                </a>
            </td>
            <td align="center">
                <a href="https://github.com/magic-peach">
                    <img src="https://avatars.githubusercontent.com/u/146705736?v=4" width="60;" alt="magic-peach"/>
                    <br />
                    <sub><b>Akanksha Trehun</b></sub>
                </a>
            </td>
		</tr>
	<tbody>
</table>
<!-- readme: contributors -end -->

---

<p align="center">
  Built with ❤️ by BITS-Rohit and the CamouChat community
</p>
