# Security & Usage Guidelines

CamouChat provides powerful browser automation and stealth infrastructure. With this power comes the responsibility to use it ethically and in compliance with the rules of the platforms you interact with.

## 🟢 Acceptable Use
- **Research & Prototyping:** Analyzing web layouts, network behavior, or creating proof-of-concept internal tools.
- **Personal Automation:** Automating repetitive personal tasks such as generating daily reports for yourself.
- **Learning & Security Testing:** Understanding fingerprinting techniques and testing your own infrastructure against automated agents.

## 🔴 Prohibited Use
- **Spam or Bulk Messaging:** Sending unsolicited messages, advertisements, or mass communications.
- **Terms of Service Violations:** Any behavior strictly prohibited by the target platform's user agreement (e.g., WhatsApp ToS).
- **Harmful or Malicious Automation:** Scraping sensitive user data, automated harassment, or attempting to bypass security safeguards maliciously.

## 🛡️ Best Practices
- **Always use Test Accounts** before deploying scripts on primary or mission-critical phone numbers.
- **Enable Rate Limiting** to avoid burst-sending and naturalize request intervals.
- **Use Residential Proxies** with GeoIP matching to ensure your automation context matches your hardware fingerprint.
- **Never store credentials in plaintext.** Use the built-in AES-256 encrypted storage modules provided by CamouChat.

## 🔐 Data & Privacy
- **Local-First:** CamouChat operates entirely on your local machine.
- **Zero Telemetry:** We do not track, collect, or transmit your data, browsing history, or message content to any external entity.
- **Encryption at rest:** All cached messages and session data are stored locally using AES-256-GCM encryption.

## ⚖️ Disclaimer
CamouChat is provided "AS IS" for educational and research purposes. 
* There is **no guarantee of undetectability**. Automated systems evolve constantly.
* The maintainers are **not responsible** for account bans, data loss, or legal consequences resulting from the misuse of this framework. Use at your own risk.
