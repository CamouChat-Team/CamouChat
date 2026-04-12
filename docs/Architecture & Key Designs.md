## 🏗️ Architecture

```text
camouchat/
├── BrowserManager/          # Anti-detect browser core: Camoufox, Fingerprinting, Profiles
│   ├── camoufox_browser.py       # Async Camoufox browser lifecycle + multi-profile PID map
│   ├── browserforge_manager.py   # BrowserForge fingerprint generation, screen-match & caching
│   ├── profile_manager.py        # Profile CRUD, encryption key management, activation lifecycle
│   ├── profile_info.py           # ProfileInfo dataclass — the canonical state object per profile
│   ├── browser_config.py         # BrowserConfig dataclass used by CamoufoxBrowser
│   └── platform_manager.py       # Platform enum (WHATSAPP, ARATTAI, …)
│
├── WhatsApp/                # Full WhatsApp Web automation layer
│   ├── login.py                  # QR-code + phone number (code-based) authentication
│   ├── chat_processor.py         # Chat sidebar scraping & CDP-based click
│   ├── message_processor.py      # Message extraction, AES-256 encryption, dedup, storage
│   ├── human_interaction_controller.py  # Realistic typing, clipboard-safe paste, clean-input
│   ├── media_capable.py          # Attachment menu + OS file-chooser interception
│   ├── reply_capable.py          # Targeted message reply via JS edge-click + humanized typing
│   ├── web_ui_config.py          # All WhatsApp DOM selectors (WebSelectorConfig)
│   └── models/                   # Chat & Message dataclasses
│       ├── chat.py
│       └── message.py
│
├── Interfaces/              # Abstract contracts — every platform must implement these
│   ├── browser_interface.py
│   ├── browserforge_capable_interface.py
│   ├── chat_processor_interface.py
│   ├── message_processor_interface.py
│   ├── login_interface.py
│   ├── media_capable_interface.py   # MediaType enum + FileTyped dataclass live here
│   ├── reply_capable_interface.py
│   ├── storage_interface.py
│   ├── human_interaction_controller_interface.py
│   ├── chat_interface.py
│   ├── message_interface.py
│   └── web_ui_selector.py
│
├── StorageDB/               # Async SQLAlchemy storage with background queue writer
│   ├── sqlalchemy_storage.py     # SQLAlchemyStorage (SQLite / PostgreSQL / MySQL)
│   ├── models.py                 # Message ORM model with encryption + composite indexes
│   └── storage_type.py           # StorageType enum (SQLITE, MYSQL, POSTGRESQL)
│
├── Encryption/              # Out-of-the-box AES-256-GCM message & chat-name encryption
│   ├── encryptor.py              # MessageEncryptor (encrypts body, returns nonce+ciphertext)
│   ├── decryptor.py              # MessageDecryptor (decrypts, auto-verifies auth tag)
│   └── key_manager.py            # KeyManager (PBKDF2-HMAC key derivation + random key gen)
│
├── Filter/                  # Rate-limiting message filter
│   └── message_filter.py         # MessageFilter (deliver / defer / drop per-chat state machine)
│
├── Decorators/              # Reusable async decorators
│   └── Chat_Click_decorator.py   # @ensure_chat_clicked — guaranteed chat open before fetch
│
├── Exceptions/              # Structured exception hierarchy
│   ├── base.py                   # CamouChatError + shared base classes
│   └── whatsapp.py               # Full WhatsApp error tree (Chat / Message / Login / Media / Reply)
│
├── NoOpPattern.py           # NoOpStorage + NoOpMessageFilter — safe opt-out stubs
├── camouchat_logger.py      # CamouChatLogger — color console + rotating file + JSON + profile-aware
├── directory.py             # DirectoryManager — OS-independent path resolver (via platformdirs)
└── __init__.py
```

---

### Key Design Decisions

- **Interface-Driven**: Every platform module implements strict abstract contracts (`ChatProcessorInterface`, `MessageProcessorInterface`, etc.) defined in `Interfaces/`. This enforces consistent APIs and makes adding new platforms clean.
- **Singleton-per-Page**: WhatsApp classes (`ChatProcessor`, `MessageProcessor`, `Login`, `MediaCapable`, `InteractionController`, `HumanInteractionController`) use `WeakKeyDictionary[Page, Self]` to guarantee exactly one instance per Playwright `Page`. The instance is garbage-collected automatically when the page closes.
- **Dependency Injection**: All classes accept a `log` parameter so you can inject the built-in `camouchatLogger`, a profile-scoped logger from `get_profile_logger()`, or any standard Python `Logger`/`LoggerAdapter` for full testability.
- **Sandboxed Profiles**: The `ProfileManager` creates one fully isolated directory per `(Platform, profile_id)` pair — separate cookies, browser cache, fingerprint, and database. Multiple bots can run on the same machine with zero data leakage between them.
- **Encrypted Storage**: AES-256-GCM encryption is a one-call opt-in (`pm.enable_encryption(...)`). Message bodies are wiped from plaintext the moment they are encrypted; chat names are HMAC-indexed so database queries remain functional without exposing real names.
- **Async-First**: The entire stack — DB writes (`asyncio.Queue`-backed background writer), Playwright page interactions, filtering, and profile lifecycle — is fully non-blocking.
- **Fingerprint Matching**: `BrowserForgeCompatible` loops until it generates a fingerprint whose screen resolution matches the host machine's actual display within 10% tolerance (up to 10 retries). This prevents mismatched viewport fingerprints from triggering bot detection.
- **CDP-Native Clicks**: `ChatProcessor._click_chat()` and `InteractionController._side_edge_click()` bypass Playwright's actionability checks entirely using raw CDP mouse events derived from live JavaScript `getBoundingClientRect()` calls — immune to WhatsApp's virtual-scroll–induced DOM node detachment.
- **NoOp Safety Net**: Both `storage_obj` and `filter_obj` in `MessageProcessor` default to `NoOpStorage` and `NoOpMessageFilter` when not provided, so the processor works without any database or filter configured.
- **Anti-Detection**: Built natively on Camoufox (patched Firefox), with BrowserForge spoofed screen-matched fingerprints, randomized mouse delays, and `geoip=True` for realistic GeoIP headers.
