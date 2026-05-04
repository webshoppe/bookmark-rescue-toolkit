# Contributing to Bookmark Rescue Toolkit

Thanks for your interest in improving Bookmark Rescue Toolkit!

This project welcomes contributions for new browsers, bug fixes, documentation, and quality‑of‑life improvements.

---

## How to get started

### 1. Fork and branch

1. Fork the repository on GitHub.
2. Clone your fork and create a feature branch:

   ```bash
   git clone https://github.com/<your-user>/bookmark-rescue-toolkit.git
   cd Bookmark-Rescue-Toolkit
   git checkout -b feature/my-change
   ```

3. When your changes are ready, open a Pull Request against `main`:
   - Use a descriptive title.
   - In the body, explain **what** changed and **why**.
   - If the change is user‑visible, mention which docs (if any) you updated.

---

## Development environment

- Python **3.10+** (developed and tested on 3.12).
- Create and activate a virtual environment:

  **Windows:**

  ```bash
  py -3.12 -m venv .venv
  .venv\Scripts\activate
  ```

  **macOS / Linux:**

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

- Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```

The only external runtime dependency is `customtkinter`; everything else comes from the Python standard library.

See the main [README](README.md) for the Quick Start and project overview.

---

## Project layout (high level)

Key files and folders:

- `gui.py` - unified GUI; main entry point when running from source.
- `core/` - engines and utilities:
  - `retriever.py` - Stage 1: scan & extract, writes `manifest.json`.
  - `json_to_html.py` - Stage 2a: Chromium JSON → Netscape HTML.
  - `sqlite_to_html.py` - Stage 2b: Firefox SQLite → Netscape HTML.
  - `vault_builder.py` - Stage 3: batch convert + HTML dashboard.
  - `bookmark_merger.py` - Stage 4: merge, deduplicate, CSV/JSON export.
  - `search.py` - search across all sources.
  - `archive_beautifier.py` - alternate styled HTML archive.
  - `utils.py` - shared helpers (e.g. `get_human_date`).
- `docs/` - Markdown documentation:
  - `GUI_WALKTHROUGH.md` - GUI usage and troubleshooting.
  - `MANUAL_TOOLS.md` - CLI reference and scripting info.
  - `CUSTOMIZATION.md` - adding browsers, themes, icons, and new GUI tabs.
- `BUILDING.md` - building the portable `.exe` with PyInstaller.
- `sandbox/` - Windows Sandbox screenshot/demo environment (optional; not in dist builds).

---

## Reporting bugs

When filing a bug report (or using the **Bug report** issue template), please include:

- **Environment:**
  - Windows version (e.g. Windows 10 LTSC, Windows 11).
  - Whether you used the portable `.exe` or ran from source.
  - Bookmark Rescue Toolkit version (`Help → About` or `core/version.py`).
- **What you did:**
  - Which tab or CLI command you used.
  - Exact paths you entered (mask any sensitive parts if needed).
- **What you saw:**
  - Error messages from the GUI log (use **Export Log**) or CLI output.
  - Screenshots if the GUI behaved unexpectedly.

Link to relevant docs if you can (for example, sections in `GUI_WALKTHROUGH.md` or `MANUAL_TOOLS.md` that you followed).

---

## Feature requests

Useful feature requests include:

- Support for additional browser variants.
- New export formats or filters (for example, date‑range exports, regex search).
- UX improvements that make recovery easier for non‑technical users.

When opening a feature request (or using the **Feature request** issue template), please explain:

- **Problem:** What you’re trying to achieve or what feels painful today.
- **Proposal:** What you’d like the toolkit to do differently.
- **Context:** Any example paths, workflows, or tools you integrate with.

---

## Adding support for a new browser

For most contributions, this is the main “code” path. In summary (full details are in [`docs/CUSTOMIZATION.md`](docs/CUSTOMIZATION.md)):

1. **Identify the engine**

   - Chromium‑family - JSON `Bookmarks` file under a `User Data` profile.
   - Gecko‑family - SQLite `places.sqlite` in a `Profiles` folder.

2. **Add an AppData path in `core/retriever.py`**

   - Extend the appropriate dictionary (`_CHROMIUM_PATHS` or `_GECKO_PATHS`) with the browser name
     and its `AppData\...` path as described in the customization guide.

3. **(Optional) Add the browser to the GUI**

   - Update the browser dropdown lists in `gui.py` so users can select it by name on Tabs 2 and 3.

4. **Test the full pipeline**

   - Run the Extractor against a profile that actually uses this browser.
   - Confirm:
     - the browser appears in `manifest.json`,
     - Vault Builder, Merger, and Search can process its bookmarks,
     - imports work in at least one mainstream browser.

When submitting a PR, mention the browser(s) added, and include any limitations you encountered.

---

## Documentation improvements

Documentation is a first‑class part of this project. Good doc PRs include:

- Clarifying confusing steps in the GUI walkthrough or CLI manual.
- Fixing typos, broken links, or out‑of‑date paths.
- Adding small troubleshooting notes based on real‑world use.

If you change CLI behavior or add new flags, please update:

- `docs/MANUAL_TOOLS.md`, and
- the CLI quick reference in `README.md`.

---

## Coding guidelines

- Prefer type hints on new or edited functions, especially in `core/`.
- Keep core logic and UI separate:
  - New parsing/merging/search behavior should go under `core/`, not directly in `gui.py`.
- Public functions in `core/` should:
  - return a dict with at least `status` and `warnings` (and additional fields as appropriate),
  - raise typed exceptions (`FileNotFoundError`, `ValueError`, `RuntimeError`, `PermissionError`) for hard failures.
- For recoverable per‑item issues, add a string to `warnings` instead of raising, so callers get a complete picture.

Before opening a PR, please ensure your code:

- passes basic linting (`flake8` / `ruff`, if configured), and
- does not introduce new unhandled exceptions in common workflows.

---

## Building the portable .exe (optional)

If your change affects packaging or you want to test the portable build:

```bash
python build.py --clean --zip
```

This produces:

- `dist/Bookmark-Rescue-Toolkit/BookmarkRescue.exe`
- `dist/BookmarkRescue_vX.Y.Z.zip`

See `BUILDING.md` for details.

You do **not** need to include built artifacts in your PR; they are generated as part of the release process.

---

## Release process (maintainers)

1. Update `core/version.py` using semantic versioning (e.g. `1.0.0`, `1.0.1`, `1.1.0`, `1.0.0-rc.3`).
2. Add a new entry to `CHANGELOG.md` for the version.
3. Run `python build.py --clean --zip`.
4. Create or update the Git tag (`vX.Y.Z`).
5. Draft a GitHub Release for the tag and attach `BookmarkRescue_vX.Y.Z.zip`, using the changelog entry as the release notes.

Thank you for contributing!
