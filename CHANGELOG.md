# CHANGELOG

All notable changes to Bookmark Rescue Toolkit will be documented in this file.

The project follows [semantic versioning](https://semver.org/spec/v2.0.0.html) in the form `MAJOR.MINOR.PATCH` with optional pre‑release tags (for example, `-beta`, `-rc.0`) for release candidates. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
-  CLI Sandbox - scripts for the Windows Sandbox screenshot environment.

### Changed
_No changes yet._

### Fixed
_No changes yet._

---

## [1.0.0-rc.2] - 2026-05-04

### Changed

- Enhanced `README.md` with badges, clearer wording, and a table of contents.
- Refined `BUILDING.md` for clarity, corrected zip naming, and added a table of contents.
- Improved `SANDBOX_README.md` with a table of contents and streamlined quick start.
- Updated `GUI_WALKTHROUGH.md` with a table of contents for easier navigation.
- Enhanced `MANUAL_TOOLS.md` with a table of contents and a clearer Supplemental Tools section.
- Adjusted the in‑app **View Docs** viewer (`gui.py`) to strip GitHub badges and inline HTML
  so README and other docs render cleanly inside the GUI.

### Added

- `.gitignore` rules to ignore sandbox mock data (`sandbox/Windows.old/`), preventing accidental commits of generated test content.
- `CONTRIBUTING.md` with project contribution guidelines and development workflow.
- GitHub issue templates for:
  - bug reports,
  - feature requests, and
  - questions/other topics,
  plus configuration to require one of these templates when opening a new issue.

---

## [1.0.0-rc.1] - 2026-05-02

### Changed

- Renamed “Screenshot Sandbox” references to “BRT Sandbox Guide” for consistent terminology.
- Expanded `SANDBOX_README.md` with detailed usage instructions and workflow steps.
- Added a table of contents to `CUSTOMIZATION.md` and clarified customization workflows.
- Refactored formatting in `MANUAL_TOOLS.md` for consistency and readability.
- Updated `GUI_WALKTHROUGH.md` to better explain Administrator requirements and recommended workspace layout.
- Aligned Python version wording and zip‑file naming across documentation.
- Refined `README.md` content to match the current feature set and documentation structure.

---

## [1.0.0-rc.0] - 2026-05-01

### Highlights

Initial import of the project into this repository.

### Added

- Core project files:
  - `core/` engines (`retriever`, converters, vault builder, merger, search, archive beautifier).
  - `gui.py` unified GUI and supporting modules.
  - `build.py`, `bookmark_rescue.spec`, and packaging assets.
- Initial documentation set:
  - `docs/` (GUI walkthrough, manual tools, customization guide).
  - `sandbox/` folder and scripts for the Windows Sandbox screenshot environment.
  - `assets/screenshots/` with `.gitkeep` to track the folder.
- Root project files:
  - `README.md`, `BUILDING.md`, `.gitignore`, `LICENSE`, `requirements.txt`, `core/__init__.py`.
- Repository housekeeping:
  - Added placeholder docs and sandbox files, then removed obsolete placeholders once real content was in place.

---

## [1.0.0-beta] - Pre-release (local development)

### Highlights

Initial pre‑release of Bookmark Rescue Toolkit.

### Added

- Windows Extractor that scans `Windows.old` or any NTFS‑formatted Windows drive and writes a structured `manifest.json`.
- JSON and SQLite converters that produce importable Netscape HTML for Chromium and Firefox‑family browsers.
- Vault Builder that generates an offline HTML dashboard.
- Bookmark Merger with deduplication and CSV/JSON export for spreadsheet and database workflows.
- Live Search tool that queries all extracted data without a conversion step.
- Offline, single‑folder portable `.exe` build using PyInstaller.

### Known limitations

- Extractor is Windows‑only; other tools require compatible files but are cross‑platform as long as you provide compatible bookmark files.

---
