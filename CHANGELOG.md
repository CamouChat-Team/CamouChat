# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-03-20

### Added

- **SEO Optimization**: Project visibility and meta-description enhancements.
- **Documentation Updates**: Refined all files in the `docs/` directory for better structural clarity.

### Fixed

- **README.md**: Addressed minor content and layout inconsistencies.

## [0.6.0] - 2026-03-13

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
