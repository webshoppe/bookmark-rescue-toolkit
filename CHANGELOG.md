# CHANGELOG

All notable changes to Bookmark Rescue Toolkit will be documented in this file.

The project follows [semantic versioning](https://semver.org/spec/v2.0.0.html) in the form `MAJOR.MINOR.PATCH` with optional pre‑release tags (for example, `-beta`, `-rc.0`) for release candidates. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
-  Joplin portable integration into `sandbox/tools`.

### Changed
_No changes yet._

### Fixed
_No changes yet._

---

## [v1.0.0-rc.4] - 2026-05-22

### Added
- Optional GUI and CLI Windows Sandbox environments for consistent screenshots, demo data, and isolated testing, with a shared overview in `sandbox/SANDBOX_README.md` and dedicated guides for each sandbox.
- Host-backed sandbox tools bundle (`sandbox/tools/`) with a central tools overview and per-tool setup guides for Firefox Portable, Notepad++, 7-Zip, PeaZip, ShareX, and SumatraPDF.

### Changed
- Refined the main README and BUILDING guide to better highlight the portable build workflow, repository structure, and release process, keeping terminology consistent with the new sandbox and tools docs.
- Normalized sandbox documentation to reference the tools overview using the non-link path `sandbox/tools/TOOLS_README.md`, avoiding broken links between `file:///` viewing and GitHub rendering.
- Updated the Firefox Portable guide to include an explicit credit and pointer to simov’s Markdown Viewer project for full usage details and troubleshooting.

### Fixed
- Clarified Windows Sandbox prerequisites and the distinction between `C:\Bookmark-Rescue-Toolkit\` (repo/app) and `C:\Bookmark_Rescue\` (workspace), reducing common setup mistakes across both sandbox readmes.
- Tightened path, casing, and wording inconsistencies in sandbox and tools documentation so folder layouts and copy/paste paths match the actual repo and host structure.

### Added / Changed (tooling)
- Extended `.gitignore` to exclude sandbox tool binaries and installers (`sandbox/tools/7zip_installer/*.exe`, `sandbox/tools/ShareX/*.exe`, Firefox, Notepad++, SumatraPDF, PeaZip portable folders and Notes folder), ensuring local sandbox tooling is never committed.
  
---

## [1.0.0-rc.3] - 2026-05-08

### Added

- New `sandbox/SANDBOX_README.md` overview describing both sandbox types,
  shared mock data, host folder layout, and shared troubleshooting.
- Dedicated GUI and CLI sandbox guides:
  - `sandbox/GUI_SANDBOX_README.md` for the GUI screenshot sandbox.
  - `sandbox/CLI_SANDBOX_README.md` for the CLI screenshot sandbox and
    Python-based test environment.
- New CLI sandbox tooling in `sandbox/`:
  - `BRT_CLI_Sandbox.wsb` (offline CLI sandbox config).
  - `BRT_CLI_Sandbox_Net.wsb` (networking-enabled CLI sandbox config).
  - `Launch_CLI_Sandbox.bat` (CLI sandbox launcher).
  - `cli_launcher_inside.bat` (opens the Command Prompt window inside the sandbox).
  - `cli_sandbox_startup.bat` (scripted CLI session for screenshots).

### Changed

- Renamed the GUI sandbox configuration and launcher for clarity:
  - `BRT_Sandbox.wsb` → `GUI_Sandbox.wsb`.
  - `Launch_BRT_Sandbox.bat` → `Launch_GUI_Sandbox.bat`.
- Updated `sandbox/sandbox_startup.bat` to work as a shared startup script
  for both GUI and CLI sandboxes.
- Refined sandbox documentation across the repo:
  - `GUI_SANDBOX_README.md` now focuses solely on the GUI sandbox flow and
    links back to `SANDBOX_README.md` for shared setup.
  - `CLI_SANDBOX_README.md` documents the CLI sandbox workflow, Python
    installer requirements, and optional GUI testing inside the CLI sandbox.
- Updated the main `README.md` documentation table to reference the new
  sandbox overview, GUI sandbox guide, and CLI sandbox guide.
- Updated `Manual_Tools.md` to correct updated path

### Added / Changed (tooling)

- Extended `.gitignore` to exclude `sandbox/python_installer/*.exe` so the local
  Python 3.12 installer used by the CLI sandbox is never committed, alongside
  the existing `sandbox/Windows.old/` mock data ignore.

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
