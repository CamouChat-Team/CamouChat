# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - [Next Version]
### Moved
- Decorator Folder moved to WhatsApp/ 

### Removed 
- BrowserForge Interface removed

### Added 
- ChatModelAPI dataclass added at camouchat/WhatsApp/models/chat_api.py
- MessageModelAPI dataclass added at camouchat/WhatsApp/models/message_api.py

- **WA-JS API Layer (`wajs_scripts.py` + `wajs_wrapper.py`)**: Built a full programmatic bridge
  into WhatsApp Web's internal Webpack store — reading messages, chats, contacts, groups,
  newsletters, connection info, privacy settings, and more, all directly from browser RAM.
  No UI clicks, no scraping, zero detection surface compared to the old ChatProcessor approach.

- **Stealth Engine**: The `WPP` (wa-js) handle is injected into a hidden non-enumerable
  `window` property and the global `window.WPP` is destroyed immediately after — making it
  invisible to WA's integrity scanners while still fully accessible from our bridge.

- **Media Extraction Pipeline**: Added `decrypt_media()` and a high-level `extract_media()`
  wrapper that lifts encrypted media blobs from WhatsApp Web without triggering CDN logs.
  It reads directly from the browser's **Cache API** first (zero network cost), and only
  falls back to a CDN download if the blob hasn't been pre-cached — clearly logged as
  `[NETWORK]` so you always know which path fired.

- **`extract_media(message, save_path) → dict`**: The main entry point for media extraction.
  Pass in any raw MsgModel dict from `get_messages()` and a save path — it handles everything
  and returns a structured result: `{success, type, mimetype, size_bytes, path, view_once, used_fallback, error}`.

- **`media_save_path(message, save_dir) → str`**: Auto-generates a clean filename from the
  message's mimetype + serialized ID so you never have to name files manually.

- **MIME → Extension Map**: Covers `image/jpeg`, `image/webp`, `video/mp4`, `audio/ogg`,
  `application/pdf`, Office formats, and more — falls back gracefully by media type.

- **Modular Smoke Test Suite (`tests/smoke_test.py`)**: Replaced the old monolithic smoke test
  with a proper modular framework. Each of the 24 API tests is its own function — pick and run
  exactly what you need via CLI, prefix matching, or a hardcoded list. Tests that are known to
  hang the XMPP bridge are flagged `[ON HOLD]` and skipped automatically.

  ```bash
  uv run tests/smoke_test.py --list                    # see all tests + on-hold status
  uv run tests/smoke_test.py                           # run all runnable tests
  uv run tests/smoke_test.py test_conn_session         # run one
  uv run tests/smoke_test.py test_conn test_privacy    # run by prefix
  ```

### Changed

- `get_messages()` JS dump now converts `Uint8Array` / `ArrayBuffer` fields to base64 —
  previously `mediaKey` (stored as a raw binary buffer on freshly-arrived messages) was
  silently dropped, causing media filters to miss brand-new messages.

- `get_message_by_id()` received the same binary → base64 serialization fix.


### Fixed 
-  BrowserForge Profiles existing fingerprint validation with same platform level to prevent duplication .


## [0.6.1] - 2026-03-20

### Added

- **SEO Optimization**: Project visibility and meta-description enhancements.
- **Documentation Updates**: Refined all files in the `docs/` directory for better structural clarity.

### Fixed

- **README.md**: Addressed minor content and layout inconsistencies.

## [0.6.0] - 2026-03-20

### Added

- **Anti-Detection Browser Layer**: Integrated [Camoufox](https://github.com/daijro/camoufox) for a stealthy browser core.
- **Dynamic Fingerprinting**: Incorporated [BrowserForge](https://github.com/daijro/browserforge) for realistic browser fingerprinting.
- **Encrypted Storage**: Implemented **AES-GCM-256** encryption for secure local message and credential storage.
- **Multi-Account & Multi-Platform Support**: Enhanced support for managing multiple profiles across Linux, macOS, and Windows.
- **Database Flexibility**: Transitioned to **SQLAlchemy**, supporting SQLite, PostgreSQL, and MySQL.
- **Sandboxed Profiles**: Fully isolated directories per profile for cookies, cache, and fingerprints.
- **Humanized Interaction Layer**: Mimicking real user behavior to reduce detection risks.
- **Dedicated CamouChat Logger**: Color console, rotating file, and JSON logging.
- **OS-Independent Directory Resolve**: Internal management of platform-specific directories.

### Changed

- Major architectural shift to an **interface-driven** design for easier extensibility.
- Improved test coverage to >= 76%.
- Fixed reports for MYPY, Black, Ruff, and deptry.

### Migrated

- **0.1.5 -> 0.6.0**: Significant codebase overhaul, moving from basic automation to a comprehensive, stealth-focused SDK.

## [0.1.5] - 2026-02-01

### Changed

- Final release in the 0.1.x series before the 0.6 core infrastructure overhaul.
