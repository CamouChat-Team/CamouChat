![Project Banner](assets/OSCG_Banner.jpeg)

# CamouChat
![img.png](assets/CamouChat_Logo.png)

**Old Name Twekaio-sdk , New Name : CamouChat** 

[![PyPI Downloads](https://static.pepy.tech/personalized-badge/tweakio-sdk?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/tweakio-sdk)
[![PyPI - Version](https://img.shields.io/pypi/v/tweakio-sdk?label=tweakio-sdk)](https://pypi.org/project/tweakio-sdk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tweakio-sdk)](https://pypi.org/project/tweakio-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-%3E90%25-brightgreen)](https://github.com/BITS-Rohit/tweakio-sdk)

---

## Why CamouChat ?

WhatsApp automation is broken:

before looking back into why camouchat . lets explore some already defined libraries. 
1. [pywhatkit](https://github.com/Ankit404butfound/PyWhatKit) This is a famous python WhatsApp kit via that we can automate our whatsapp simply and nicely. Last commit = 2 years ago still other libs that exist gives better benefits.
But what if selectors based breaks now ? what if number used got banned ? where is number safety. also we cannot save sessions and require u to again and again login , messed up not good for long term. and no Profiles etc setup.
2. [pywhatsapp](https://github.com/tax/pywhatsapp) it requires some yowsup stuff , I did not understand about is it safe or not ? no solid proof of verified source of long term access, also where is reliability again ? i was not convinced as it had commits some freaking 11 years so i gone for next Explore searches. 
3. [webwhatsap-wrapper](https://github.com/mukulhase/WebWhatsapp-Wrapper) it has good document, but freaking 6 years ago last commit, and again not worked very good , so my only option is to look around again for next option. 
4. [alright](https://github.com/Kalebu/alright?tab=readme-ov-file) It also explains simply why alright but again last commit 3 years ago . Simple native APIs it gives, but not looked promising if any error raised up as i want reliable source of truth which i think many wants. Also it did saves and hanle login etc. but mulitple Profiles etc fingerprinting how it will handle? is it safe against Number ban ? how deeply it connects to drivers , i did not see any of this security and hence liability.  
5. [WAHA](https://github.com/devlikeapro/waha) it is very famous lib for fast automating WhatsApp web , from docs and readme.md it is sure that it is fast against a browser automation based approacch , but recently it a large number of users got hacked cuz of some leaking API securty , it requires some setup too and kind of hard and u would  need to understand a lot of networking if u are like wondering is it really good and whats the best setup u can make with WAHA. But again it just wraps around web whatsapp API , but no account safety or other security , or any profile | Multi-profile Handling.

hence after all these libs explore i got to know , that we can trade off the fast API like WAHA with stealth profiles that can manage profiles internally and i would not need to do much work. 
Thats where CamouChat-sdk comes in. Its not just library , it's  Published on PYPI and packaged as SDK . 

--- 
## Benefits 

Here First of all we are not gonna make an API wrapper cuz WAHA already does that but we can make a trade off of that fast API wrapping to browser automation
capabilities with solving all the other issues that those browser automation libs had. 
1. CamouChat uses [Camoufox Browser](https://github.com/daijro/camoufox) which is a patched version of [Playwright](https://github.com/microsoft/playwright-python)'s firefox browser. Camoufox is still an active repo and a well known open source anti-detect browser.
2. CamouChat also uses [BrowserForge](https://github.com/daijro/browserforge) it provides random fingerprint dataclasses to send directly into the camoufox. 
3. CamouChat gives Multi-profile Handling easily for users to directly start the profiles. 
4. CamouChat gives Encryption and Decryption system (AES GCM 256) for storing messages internally with Encryption so that if any security breach happens the core messaging still holds the privacy and do not let the Account messages get leaked.
5. CamouChat uses [sql alchemy](https://github.com/sqlalchemy/sqlalchemy) it directly provides us safe sql handling against any sql injection and other attacks. Parameterized insertion , and support all type of sql databases. ( Also an active repo ).
6. CamouChat uses Sandboxing Every Browser to keep fingerprint remain stealth. And able to create new Fingerprint without being mixed with other profiles.
7. CamouChat is based on Playwright browser which self handles Session saving and updating internally and reliably
8. CamouChat's scopes is not just to provide this , it has scope to keep maintaining it and also adding all other famous messaging platform into it so that devs do not need to learn new libs for diff platform. It works on a singular Architecture to remain easy for devs.
9. CamouChat will also be inheriting Stable Techniques used by older libs so that it can provide all the best cherry-picks from all , Not just one.
10. CamouChat has internal rate limiting mechanism that you can use while making ur Bot | Agent Apps. 
11. CamouChat also has Humanized typing and Humanized mouse to face ML based Long Term Detection proof. It auto rotates the time and all making you u do not worry about how to make it manually.
12. CamouChat stores nothing on its own side | nothing sends outside -> it all saves the data on ur device. 
13. CamouChat is OS independent from automating browser to upto saving data to correct professionalism directory according to OS ( Linux | MacOS | Windows).


---


---

## 📦 Installation



## 🏗️ Architecture

```
# --- Down below is old Must be Updated.
tweakio-sdk/
├── src/
│   ├── BrowserManager/     # Anti-detect Playwright + Camoufox
│   ├── WhatsApp/           # Platform-specific implementation
│   │   ├── login.py        # QR + Phone authentication
│   │   ├── chat_processor.py
│   │   ├── message_processor.py
│   │   ├── web_ui_config.py  # Selector definitions
│   │   └── DerivedTypes/   # Chat, Message dataclasses
│   ├── Interfaces/         # Abstract contracts (for future platforms)
│   ├── StorageDB/          # Async SQLite with queue workers
│   └── Exceptions/         # Custom exception hierarchy
└── tests/                  # >90% coverage on core modules
```


---

### 🗺️ Roadmap

### v0.6 — Core Infrastructure
- [✅] Dedicated CamouChat Logger 
- [✅] Multi-Account  & Multi-Platform Support Added
- [✅] SandBoxed Browser and Profile Isolation Supported
- [✅] SQL based Security Attacks safe [Uses SQL Alchemy]
- [✅] Supports OS independent Directory resolve internally
- [✅] Encryption & Decryption of messages & Chats.
- [✅] Tests Coverage >=76% and MYPY , Black , Ruff, deptry Reports Fixed

----- Shipped  V0.6 on [PYPI]()
### v0.7 — WebSelector Stability Techniques 
- [ ] Cherry Picked stable Selector Techniques 
- [ ] WhatsApp Stability Increase
- [ ] Tests >=80% & Lint Checking Updated.

### v0.8
- [ ] Saving Media from whatsapp to local Feature
- [ ] WebUI Hardening
- [ ] Tests >=85% & Lint Checking updated.

### v0.9
- [ ] Extra WhatsApp Functions 
- [ ] Internal Stability Focused

### v1.0 forward — arattai (Coming Soon)
- [ ] arattai Platform Next Integration

---

### ❓ FAQ

**Q: Will I get banned?**  
A: It is rare but can happen on the least. Some preventions is that always use rate limiter given by the sdk. Dont spam. It uses Patched Browser so even if have to be done something it will be a soft ban [Soft ban : Browser gets logged out Not direct number ban : Tested with real numbers.]. Still if u have a spare account use that first for 100% safe.

**Q: Can I use this for spam?**  
A: No. This SDK is for legitimate automation for devs | agents | Small Business Model Testing .Doing spam may risk ur number , Try at ur own risk.

**Q: Why not just use the WhatsApp Business API?**  
A: Business API has message template restrictions and approval processes. Cost for every freaking message . You would need to verify urself first. 
Also limited behavior.We automate the web itself. **-- Free and Open Source**

---

### 📄 License

MIT License — see [LICENSE](LICENSE)

### Important Notes 

* CamouChat-sdk is for Education | devs | Agents creating | Business Prototypes Not for Commercial usage. It does not encourage Platform ToS violation.
* Commercial usage is strictly prohibited. 


_Built with ❤️ by BITS-Rohit and the CamouChat-sdk community_
