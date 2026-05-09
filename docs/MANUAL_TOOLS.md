# Manual CLI Tools

Every engine in `core/` runs independently from the command line - no GUI, no display required. This makes the toolkit scriptable, automatable, and usable in headless or server environments.

> This guide is aimed at advanced users and automation scripts.  
> If you only use the GUI, you can safely skip this document.

**Run all commands from the repository root** with your virtual environment active.

## Table of contents

- [Pipeline overview](#pipeline-overview)
- [Running with the `-m` flag](#running-with-the--m-flag)
- [Stage 1: Retriever](#stage-1-retriever)
- [Stage 2a: JSON Parser](#stage-2a-json-parser)
- [Stage 2b: SQLite Parser](#stage-2b-sqlite-parser)
- [Stage 3: Vault Builder](#stage-3-vault-builder)
- [Stage 4: Bookmark Merger](#stage-4-bookmark-merger)
- [Search engine](#search-engine)
- [Archive Beautifier (CLI-only)](#archive-beautifier-cli-only)
- [Supplemental tools](#supplemental-tools)
- [Scripting and automation](#scripting-and-automation)

---

## Pipeline Overview

```
core/retriever.py
    Scan a Windows drive → copy raw browser files + write manifest.json
        │
        ├── core/json_to_html.py        (one Chromium JSON → Netscape HTML)
        ├── core/sqlite_to_html.py      (one Firefox SQLite → Netscape HTML)
        │
        ├── core/vault_builder.py       (batch → Netscape HTML dashboard)
        ├── core/bookmark_merger.py     (batch → merged HTML / CSV / JSON)
        ├── core/search.py              (search across all sources)
        └── core/archive_beautifier.py  (batch → styled HTML5 archive)
```

The single-file converters (Stages 2a/2b) are completely independent of Stage 1 - feed them any compatible file from any source.

---

## Running with the `-m` flag

Always use the `-m` flag from the repo root. This ensures relative imports inside `core/` resolve correctly.

```bash
python -m core.retriever --help
python -m core.json_to_html --help
python -m core.sqlite_to_html --help
python -m core.vault_builder --help
python -m core.bookmark_merger --help
python -m core.search --help
python -m core.archive_beautifier --help
```

---

## Stage 1: Retriever

**Module:** `core/retriever.py`  
**Purpose:** Scan a Windows installation and copy all bookmark artifacts into a structured output folder.

### Syntax

```
python -m core.retriever <source> <output> [--verbose]
```

| Argument | Required | Description |
|---|---|---|
| `source` | ✅ | Windows.old root, or any drive root (`D:\`) |
| `output` | ✅ | Destination folder (created if absent) |
| `--verbose` / `-v` | - | Print each copied file as it is processed |

### Examples

```bash
# Scan a Windows.old folder
python -m core.retriever "C:\Windows.old" "C:\Recovery\Raw"

# Scan a secondary hard drive
python -m core.retriever D:\ "C:\Recovery\Raw"

# Verbose - see every file as it is copied
python -m core.retriever "C:\Windows.old" "C:\Recovery\Raw" --verbose
```

### Output

```
Scanning : C:\Windows.old
Output   : C:\Recovery\Raw

Scan complete.
  Users scanned : 2
  Files copied  : 14

Manifest  : C:\Recovery\Raw\manifest.json
```

### What gets collected

| Artifact type | Files |
|---|---|
| `chromium_bookmarks_json` | Primary `Bookmarks` file (no extension in Chrome) |
| `chromium_bookmarks_backup` | `Bookmarks.bak` |
| `gecko_places_sqlite` | `places.sqlite` |
| `gecko_places_sqlite_wal` | `places.sqlite-wal` (unclean shutdown indicator) |
| `gecko_favicons_sqlite` | `favicons.sqlite` |
| `gecko_bookmark_backup` | `bookmarkbackups/*.jsonlz4` |

### manifest.json

Written to `output/manifest.json`. All downstream tools consume this file. It contains the full artifact inventory including types, paths, and user/browser/profile metadata.

### Error handling

| Situation | Behaviour |
|---|---|
| `Users\` directory not found | `FileNotFoundError` with a clear message |
| NTFS permission denied | Logged as a warning; scan continues |
| Cannot write `manifest.json` | Logged as a warning; other output unaffected |

For all available options, run:

```bash
python -m core.retriever --help
```

---

## Stage 2a: JSON Parser

**Module:** `core/json_to_html.py`  
**Purpose:** Convert a single Chromium `Bookmarks` file to Netscape HTML.

### Syntax

```
python -m core.json_to_html <source> <output> [--browser LABEL]
```

| Argument | Required | Description |
|---|---|---|
| `source` | ✅ | Chromium `Bookmarks` file (JSON; often no extension) |
| `output` | ✅ | Output `.html` file path |
| `--browser` | - | Label used in HTML title and link metadata (default: `"Chromium"`) |

### Examples

```bash
python -m core.json_to_html Bookmarks bookmarks.html
python -m core.json_to_html Chrome_Bookmarks.json chrome.html --browser "Google Chrome"
python -m core.json_to_html "C:\Raw\Alice\Brave\Default\Brave_Bookmarks.json" brave.html --browser "Brave"
```

### Output

```
Converted : 347 bookmarks, 28 folders
Output    : brave.html
```

### Errors

| Error | Cause |
|---|---|
| `FileNotFoundError` | Source path does not exist |
| `ValueError: not valid JSON` | File is corrupt or truncated |
| `ValueError: missing 'roots'` | Valid JSON but not a Chromium Bookmarks file |

For all available options, run:

```bash
python -m core.json_to_html --help
```

---

## Stage 2b: SQLite Parser

**Module:** `core/sqlite_to_html.py`  
**Purpose:** Convert a single Firefox-family `places.sqlite` to Netscape HTML.

### Syntax

```
python -m core.sqlite_to_html <source> <output> [--browser LABEL]
```

| Argument | Required | Description |
|---|---|---|
| `source` | ✅ | Firefox-family `places.sqlite` |
| `output` | ✅ | Output `.html` file path |
| `--browser` | - | Label used in HTML title and metadata (default: `"Firefox"`) |

### Examples

```bash
python -m core.sqlite_to_html places.sqlite bookmarks.html
python -m core.sqlite_to_html places.sqlite librewolf.html --browser "LibreWolf"
python -m core.sqlite_to_html "C:\Raw\Alice\Tor Browser\Desktop_profile.default\places.sqlite" tor.html --browser "Tor"
```

### WAL journal warning

```
  [!] A WAL journal file was detected alongside this database.
      Some recently added bookmarks could be missing from the output.
```

Informational only → the committed data is fully readable.

### Errors

| Error | Cause |
|---|---|
| `FileNotFoundError` | Source path does not exist |
| `RuntimeError: Not a valid Firefox places.sqlite` | Missing `moz_bookmarks` or `moz_places` tables |

For all available options, run:

```bash
python -m core.sqlite_to_html --help
```

---

## Stage 3: Vault Builder

**Module:** `core/vault_builder.py`  
**Purpose:** Batch-convert all extracted artifacts into Netscape HTML and generate an `index.html` dashboard for browser import.

### Syntax

```
python -m core.vault_builder <source> <output>
```

| Argument | Required | Description |
|---|---|---|
| `source` | ✅ | Folder from the Retriever (should contain `manifest.json`) |
| `output` | ✅ | Destination for the vault site |

### Examples

```bash
python -m core.vault_builder "C:\Recovery\Raw" "C:\Recovery\Vault"
python -m core.vault_builder ./raw_output ./vault_site
```

### Output

```
Raw data : C:\Recovery\Raw
Site out : C:\Recovery\Vault

Mode      : manifest
Converted : 8 page(s)

Vault ready: C:\Recovery\Vault\index.html
```

When no `manifest.json` is present the Vault Builder falls back to walking the directory tree and inferring file types from names.

For all available options, run:

```bash
python -m core.vault_builder --help
```

---

## Stage 4: Bookmark Merger

**Module:** `core/bookmark_merger.py`  
**Purpose:** Merge bookmarks from multiple sources into one deduplicated Netscape HTML file, or export to CSV/JSON for database tools.

### Syntax

```
python -m core.bookmark_merger (--raw FOLDER | -s FILE [FILE ...])
    (-o OUTPUT | --export-csv FILE | --export-json FILE)
    [--no-dedup] [--no-group]
```

| Argument | Description |
|---|---|
| `--raw FOLDER` | Read manifest.json from a Retriever output folder |
| `-s FILE …` | One or more source files (Netscape HTML, JSON, or SQLite) |
| `-o / --output` | Output merged Netscape HTML file |
| `--export-csv` | Export flat CSV (UTF-8 with BOM for Excel compatibility) |
| `--export-json` | Export JSON array |
| `--no-dedup` | Disable URL deduplication |
| `--no-group` | Disable source browser grouping in HTML output |

Multiple output flags can be combined in one call.

### Examples

```bash
# Merge all browsers from an extraction into one HTML
python -m core.bookmark_merger --raw "C:\Recovery\Raw" -o merged.html

# Merge two HTML files
python -m core.bookmark_merger -s chrome.html firefox.html -o merged.html

# Export from raw folder to CSV and JSON simultaneously
python -m core.bookmark_merger --raw "C:\Recovery\Raw" --export-csv bm.csv --export-json bm.json

# Flat merge, no dedup
python -m core.bookmark_merger --raw "C:\Recovery\Raw" -o flat.html --no-dedup --no-group
```

### Output

```
Merged HTML   : merged.html

Sources processed : 5
Input bookmarks   : 4,218
Duplicates removed: 1,327
Output bookmarks  : 2,891
```

### Deduplication behaviour

URLs are compared without regard to the http/https scheme. For example, http://example.com/page and https://example.com/page are treated as the same bookmark. When both exist, the https:// version is kept.

### CSV columns

| Column | Description |
|---|---|
| `title` | Bookmark title |
| `url` | Full URL |
| `folder_path` | Slash-separated folder hierarchy, e.g. `Toolbar / Work / Dev` |
| `source` | Browser label (e.g. `Google Chrome (Default)`) |
| `date_added` | Unix timestamp |
| `date_human` | Human-readable date, e.g. `January 01, 2023` |

### JSON structure

```json
[
  {
    "title": "Python Docs",
    "url": "https://docs.python.org/3/",
    "folder_path": ["Toolbar", "Work", "Dev"],
    "source": "Google Chrome (Default)",
    "date_added": 1672531200,
    "date_human": "January 01, 2023"
  }
]
```

For all available options, run:

```bash
python -m core.bookmark_merger --help
```

---

## Search Engine

**Module:** `core/search.py`  
**Purpose:** Search bookmarks by title or URL across all extracted sources without converting them first.

### Syntax

```
python -m core.search (--raw FOLDER | -s FILE [FILE ...]) QUERY
    [--field {both|title|url}] [--limit N] [--case-sensitive]
```

| Argument | Description |
|---|---|
| `--raw FOLDER` | Search against a Retriever output folder |
| `-s FILE …` | Search individual files |
| `QUERY` | Search term (see query syntax below) |
| `-q QUERY` | Alternative query flag for scripting |
| `--field` | `both` (default), `title`, or `url` |
| `--limit N` | Cap results (default: 0 = unlimited) |
| `--case-sensitive` | Disable case folding |

### Query syntax

All words in the query must be present (AND logic). Prefix a word with `-` to exclude it.

```bash
# Find anything with "python"
python -m core.search --raw "C:\Recovery\Raw" "python"

# Must have "python" AND "tutorial"
python -m core.search --raw "C:\Recovery\Raw" "python tutorial"

# Must have "python" but NOT "video"
python -m core.search --raw "C:\Recovery\Raw" "python -video"

# Search only URLs for a domain
python -m core.search --raw "C:\Recovery\Raw" "github.com" --field url

# Search only titles, capped at 20 results
python -m core.search --raw "C:\Recovery\Raw" "recipe" --field title --limit 20
```

### Output

```
Found 3 result(s) for 'python tutorial':

     1.  Python Tutorial — W3Schools
         https://www.w3schools.com/python/
         Source: Google Chrome (Default)  |  Folder: Toolbar / Dev
         Added:  March 15, 2022

     2.  The Python Tutorial — Python 3 Documentation
         https://docs.python.org/3/tutorial/
         Source: Firefox (abc12.default-release)  |  Folder: Unsorted Bookmarks
         Added:  June 02, 2021
```

For all available options, run:

```bash
python -m core.search --help
```

---

## Archive Beautifier (CLI-only)

**Module:** `core/archive_beautifier.py`  
**Purpose:** Alternate to the Vault Builder. Produces a responsive HTML5 archive with a dark/light theme toggle, sticky navigation, and forensic metadata. Designed for human browsing, not browser import. Requires `manifest.json`.

### Syntax

```
python -m core.archive_beautifier <source> <output>
```

### Examples

```bash
python -m core.archive_beautifier "C:\Recovery\Raw" "C:\Recovery\Archive"
python -m core.archive_beautifier ./raw_output ./stylized_archive
```

### Output

```
Converted : 8 page(s)
Bookmarks : 2,341
Folders   : 174

Archive ready: C:\Recovery\Archive\index.html
```

### Vault Builder vs. Archive Beautifier

| Feature | Vault Builder | Archive Beautifier |
|---|---|---|
| Browser import | ✅ | ❌ |
| Dark/light theme toggle | ❌ | ✅ |
| Sticky navigation with folder jump links | ❌ | ✅ |
| Forensic metadata (source path, artifact type) | ❌ | ✅ |
| External `style.css` (editable) | ❌ | ✅ |
| Back-to-index link on each page | ❌ | ✅ |

For all available options, run:

```bash
python -m core.archive_beautifier --help
```

---

## Supplemental tools

### Sandbox screenshot environment (`sandbox/`)

A Windows Sandbox environment for generating clean screenshots and demos, with realistic mock browser data laid out exactly like the examples in this manual.

**What it provides**

- Mock `C:\Windows.old\` with multiple users and browsers
- Pre-created workspace folders:
  - `C:\Bookmark_Rescue\1_Raw_Extracted_Data\`
  - `C:\Bookmark_Rescue\2_Vault_Site\`
  - `C:\Bookmark_Rescue\3_Merged\`
- Automatic launch of `BookmarkRescue.exe` inside the sandbox
- A shared `Screenshots\` folder mapped back to the host

**Setup and usage**

See [`sandbox/SANDBOX_README.md`](../sandbox/SANDBOX_README.md) for full instructions.

Typical host-side usage:

```bash
C:\Bookmark_Rescue\Sandbox\Launch_GUI_Sandbox.bat
```

**Notes**

- Requires Windows Sandbox to be enabled on the host.
- Requires the portable app to be built first via `python build.py`.
- The `sandbox/` folder is for contributors and is **not** included in the portable `.zip` distribution.

---

## Scripting and Automation

All public functions return structured dicts and raise typed exceptions, making them easy to use from other scripts.

All CLI entry points return exit code `0` on success and a non‑zero exit code on hard failure (for example, a missing source path or an unreadable `manifest.json`).  
This makes them easy to integrate into shell scripts and automation pipelines.

```python
from core.retriever          import recover_bookmarks
from core.json_to_html       import convert_json_to_html
from core.sqlite_to_html     import convert_sqlite_to_html
from core.vault_builder      import build_vault
from core.bookmark_merger    import merge_sources, export_to_csv, export_to_json
from core.search             import search_bookmarks, search_from_raw
from core.archive_beautifier import build_archive

# Full pipeline
result  = recover_bookmarks(r"C:\Windows.old", r"C:\Raw")
vault   = build_vault(r"C:\Raw", r"C:\Vault")
merged  = merge_sources([...], r"C:\merged.html")
csv_out = export_to_csv([...], r"C:\bookmarks.csv")
hits    = search_from_raw(r"C:\Raw", "python tutorial", field="title")
```

### Return value schemas

**`recover_bookmarks()`**
```python
{ "status", "copied_files", "users_scanned", "artifacts": [...], "warnings": [...] }
```

**`convert_json_to_html()` / `convert_sqlite_to_html()`**
```python
{ "status", "bookmarks", "folders", "warnings", "source", "output", "browser" }
```

**`build_vault()`**
```python
{ "status", "converted", "warnings", "entries": [...], "used_manifest" }
```

**`merge_sources()` / `export_to_csv()` / `export_to_json()`**
```python
{ "status", "total_input", "duplicates_removed", "total_output", "sources_processed", "warnings" }
```

**`search_bookmarks()` / `search_from_raw()`**
```python
[ BookmarkEntry(url, title, add_date, folder_path, source_label), ... ]
```

### Exception types

| Exception | Raised by | Cause |
|---|---|---|
| `FileNotFoundError` | All | Source path or `manifest.json` not found |
| `ValueError` | JSON Parser, Merger | Not valid JSON or not a Chromium Bookmarks file |
| `RuntimeError` | SQLite Parser, Archive Beautifier | Not a valid Firefox places database |
| `PermissionError` | Retriever | Cannot read the top-level `Users` directory |

> All public functions return structured dictionaries and raise clear exceptions. This makes the tools easy to use in scripts or other automation.
