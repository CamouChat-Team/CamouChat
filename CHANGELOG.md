# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.7.0] — Unreleased

### Added

- **License Compliance**: Introduced a `NOTICE` file and correct Apache 2.0 attribution headers for the bundled `wa-js` integration.
- **RAM-Level Bridge**: Implemented a comprehensive internal JavaScript bridge for real-time access to messages, chats, contacts, and privacy state — eliminating all DOM scraping.
- **Stealth Engine**: Hardened the bridge with non-enumerable, randomly-keyed property handles to resist WhatsApp integrity scanner enumeration.
- **Media Extraction Pipeline**: Introduced `save_media` with automatic type-based categorisation (image, video, audio, document, sticker) and local-first retrieval prioritising the browser LRU cache over CDN calls.
- **Message Event Hook**: Added the `@msg_event_hook` decorator for zero-latency, asynchronous interception of incoming WhatsApp messages.
- **Extended Data Models**: Expanded `ChatModelAPI` and `MessageModelAPI` to achieve full schema parity with internal WhatsApp structures.
- **Unified Boolean Direction**: Introduced type-safe `fromMe` boolean across all models and storage layers, replacing legacy string-based `direction` literals.
- **Normalized Attribute Schema**: Standardized `Chat` and `Message` models with `id_serialized`, `name`, and `ui` fields for cross-platform consistency.
- **Contextual Reply**: Integrated `WapiSession` into `InteractionController`, enabling precise message quoting via DOM-focus fallback and scroll-to-message support.
- **Bridge API Parity**: Added `mark_is_composing` and `decrypt_media` methods to the `WAJS_Scripts` layer, completing the internal API surface.
- **Test Infrastructure**: Decoupled interactive E2E and smoke validation scripts from the automated Pytest suite, enabling clean CI/CD execution without live browser dependencies.

### Changed
- **Interfaces to Contracts** : Moved all interfaces to contracts , simpler organisation.
- **Storage Architecture Hardening**: Refactored `SQLAlchemyStorage` into a normalized ingestion pipeline supporting both Browser (DOM) and API (RAM) message sources.
- **Type-Safe Filtering**: Rebuilt `MessageFilter` to utilize `id_serialized` for deterministic message identification and deduplication.
- **Media API Contract**: Unified the `extract_media` return schema across `WapiWrapper`, `MessageApiManager`, and `MediaCapable`, providing consistent structured output including success state, file path, MIME type, byte size, and cache/CDN latency telemetry.
- **Module Organisation**: Relocated decorator modules into the `WhatsApp/` package for improved structural cohesion.
- **Binary Serialisation**: Improved `Uint8Array`-to-base64 handling in message fetching to ensure reliable `mediaKey` and media metadata extraction.

### Fixed

- **Static Analysis**: Resolved all Mypy type errors across 82 source files via protocol stubs, strict assertions, and corrected Liskov substitution principle violations.
- **Unit Test Parity**: Restored 100% pass rate across the full test suite by aligning mocks with the updated attribute naming and boolean logic.
- **Manager Instantiation**: Fixed critical initialization bug in `WapiSession` ensuring all API managers receive the required browser page references.
- **Concurrent Logging**: Hardened `camouchat_logger` with a graceful conditional import for `concurrent-log-handler`, falling back to a standard rotating handler when unavailable.
- **Unit Tests**: Corrected `InteractionController` test suite to reflect method renames and updated mock object requirements introduced during the `quote_only` API refactor.
- **Initialisation**: Fixed indentation errors and potential initialisation races in `CamoufoxBrowser` and `ProfileManager`.

### Removed

- **Diagnostic Verbosity**: Stripped redundant media debug output from `MessageModelAPI.__str__` to produce clean, production-safe log lines.
- **Legacy Scraping Layer**: Removed the monolithic `ChatProcessor` DOM scraper and the first-generation `BrowserForge` wrapper.
- **Deprecated Attrs**: Eliminated legacy `chat_name`, `chat_ui`, and `direction` string references throughout the core messaging pipeline.

---

## [0.6.1] — 2026-03-20

### Added

- **Documentation**: Refined all files in the `docs/` directory for improved clarity and structural consistency.

### Fixed

- **README**: Addressed minor content inaccuracies and formatting inconsistencies.

---

## [0.6.0] — 2026-03-20

### Added

- **Anti-Detection Browser Core**: Integrated [Camoufox](https://github.com/daijro/camoufox) as the stealth browser foundation.
- **Dynamic Fingerprinting**: Incorporated [BrowserForge](https://github.com/daijro/browserforge) for realistic, per-session browser fingerprint generation.
- **Encrypted Storage**: Implemented AES-GCM-256 encryption for all locally persisted messages and credentials.
- **Multi-Account Support**: Full support for managing isolated profiles across Linux, macOS, and Windows.
- **Database Abstraction**: Introduced a SQLAlchemy-backed storage layer with support for SQLite, PostgreSQL, and MySQL.
- **Profile Sandboxing**: Fully isolated per-profile directories for cookies, cache, and fingerprint state.
- **Humanised Interaction**: Implemented keyboard telemetry and timing simulation to reduce behavioural detection risk.
- **Structured Logging**: Added a dedicated logger with colour console output, rotating file handler, and JSON formatter.
- **Directory Resolution**: Introduced platform-aware internal directory management.

### Changed

- **Architecture**: Transitioned to an interface-driven design pattern for improved extensibility and testability.
- **Test Coverage**: Raised automated test coverage to ≥ 76%.
- **Static Analysis**: Achieved clean passes under Mypy, Black, Ruff, and deptry.

---

## [0.1.5] — 2026-02-01

Final release in the 0.1.x series prior to the 0.6.0 core infrastructure overhaul.
