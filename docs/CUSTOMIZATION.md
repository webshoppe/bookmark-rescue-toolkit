# Customization Guide

The Bookmark Rescue Toolkit is intentionally modular. This guide covers everything from adding a new browser in two lines to swapping the window icon to extending the GUI with a new tab.

## Table of contents

- [Adding new browsers](#adding-new-browsers)
- [Custom window icon](#custom-window-icon)
- [GUI appearance](#gui-appearance)
- [Vault dashboard appearance](#vault-dashboard-appearance)
- [Bookmark Merger: search query customisation](#bookmark-merger-search-query-customisation)
- [Adding a new GUI tab](#adding-a-new-gui-tab)
- [Code architecture reference](#code-architecture-reference)

---

## Adding New Browsers

### Step 1: Identify the browser engine

| Engine | Format | How to tell |
|---|---|---|
| **Chromium-family** | JSON `Bookmarks` file | A Chrome fork - look for a `Bookmarks` file (no extension) in `User Data\Default\` |
| **Gecko-family** | SQLite `places.sqlite` | A Firefox fork - look for `places.sqlite` in a `Profiles\` folder |

### Step 2: Find the AppData path

On a live Windows machine, paste the relevant path into Explorer's address bar (for example: %LOCALAPPDATA% or %APPDATA%). Then navigate to the browser's folder and note the part that comes after AppData\Local\ or AppData\Roaming\.
- `%LOCALAPPDATA%` → most Chromium browsers live here
- `%APPDATA%` → most Gecko browsers live here

Navigate to the browser's folder and note the path after `AppData\Local\` or `AppData\Roaming\`.

### Step 3: Add to retriever.py

Open `core/retriever.py` and find the appropriate dictionary.

**Chromium-family** - add to `_CHROMIUM_PATHS`:
```python
_CHROMIUM_PATHS: dict[str, str] = {
    # ... existing entries ...
    "My New Browser": "AppData/Local/MyNewBrowser/User Data",
}
```

**Gecko-family with a Profiles/ parent** (standard Firefox layout):
```python
_GECKO_PATHS: dict[str, str] = {
    # ... existing entries ...
    "My Firefox Fork": "AppData/Roaming/MyFirefoxFork/Profiles",
}
```

**Gecko-family with a single fixed profile** (like Tor's `profile.default`):
```python
    "My Single Profile Browser": "AppData/Local/MyBrowser/Data/Browser/profile.default",
```

Use forward slashes - `pathlib` handles the separator on every OS, and forward slashes work correctly in raw strings without the `\\` confusion.

### Step 4: Add to the GUI dropdown (optional)

Open `gui.py`, find `_build_converter_tab`, and add to the relevant list:

```python
json_browsers = [
    # ... existing entries ...
    "My New Browser",         # Chromium
]

sqlite_browsers = [
    # ... existing entries ...
    "My Firefox Fork",        # Gecko
]
```

### Disabling browsers to speed up scans

Comment out any browser you don't need:

```python
_CHROMIUM_PATHS: dict[str, str] = {
    "Google Chrome":   "AppData/Local/Google/Chrome/User Data",
    # "Chrome Beta":   "AppData/Local/Google/Chrome Beta/User Data",
    # "Chrome Dev":    "AppData/Local/Google/Chrome Dev/User Data",
}
```

This reduces the number of filesystem `exists()` checks per user profile and noticeably speeds up scans on drives with many user accounts.

This optimization only affects the **Extractor** (Stage 1).  
You can still convert exported `Bookmarks` or `places.sqlite` files manually via Tabs 2 and 3, or directly through the CLI tools, even if a browser has been commented out here.

---

## Custom Window Icon

<p align="center">
  <img src="../assets/screenshots/08-custom-window-icon-win10-taskbar.png" width="550" alt="The Windows taskbar displaying the custom icy-white and blue Bookmark Rescue Toolkit folder icon">
  <br><em>Replacing the default executable icon to perfectly match your local desktop aesthetic.</em>
</p>

The app looks for an icon file next to `gui.py` on every launch. Place either of these files in the repository root:

| File | Used on | Notes |
|---|---|---|
| `icon.ico` | Windows (native, preferred) | Multi-resolution ICO recommended |
| `icon.png` | Windows, macOS, Linux | Fallback for all platforms |

On Windows, `icon.ico` is tried first. If absent, `icon.png` is used. If neither exists, the default Tkinter icon shows silently - no error, no crash.

When building with `build.py`, both `icon.ico` and `icon.png` are automatically copied into the final `Bookmark-Rescue-Toolkit` folder.

### Recommended specifications

| Property | Recommendation |
|---|---|
| ICO sizes | 16x16, 32x32, 48x48, 64x64, 128x128, 256x256 (all embedded in one `.ico`) |
| PNG size | 256x256 or 512x512 |
| Format | RGB or RGBA (transparency supported) |
| Color space | sRGB |

### Creating ICO files

You can create high-quality `.ico` files using free tools such as:

- [IcoFX](https://www.icofx.com/) (Windows, recommended)
- [GIMP](https://www.gimp.org/) (Windows, macOS, Linux)
- [ImageMagick](https://imagemagick.org/) (command line):

```bash
# Convert a PNG to a multi-resolution ICO with all standard Windows sizes
magick input.png -define icon:auto-resize="256,128,64,48,32,16" output.ico
```

> **Tip:** Your source PNG should be at least 256x256 for sharp results at all sizes.
> Run this command from the repository root after placing your source PNG there.

#### How it works in code

```python
def _load_icon(self) -> None:
    ico = _HERE / "icon.ico"
    png = _HERE / "icon.png"

    if sys.platform == "win32" and ico.exists():
        try:
            self.iconbitmap(str(ico))
            return   # success - no need to try PNG
        except Exception:
            pass     # malformed .ico - fall through to PNG

    if png.exists():
        try:
            img = tk.PhotoImage(file=str(png))
            self.iconphoto(True, img)
            self._icon_ref = img   # prevent garbage collection
        except Exception:
            pass     # malformed .png - default Tkinter icon used silently
```

`_HERE` is set by `_get_base_path()` which returns the folder containing `gui.py`
when running from source, or the folder containing `BookmarkRescue.exe` when running
as a portable build. This ensures icons are always found next to the executable
regardless of how or where the app was launched.

---

## GUI Appearance

### Theme and color mode

At the top of `gui.py`:

```python
ctk.set_appearance_mode("System")    # "System" | "Dark" | "Light"
ctk.set_default_color_theme("blue")  # "blue"   | "green" | "dark-blue"
```

`"System"` follows the OS dark/light mode preference. Override to `"Dark"` or `"Light"` to lock it.

### Button and accent colors

Individual widgets accept `fg_color`, `hover_color`, and `text_color`:

```python
# Example: change the run button accent color
self.ext_run_btn = ctk.CTkButton(
    tab, text="Run Extraction",
    fg_color="#7c3aed",       # violet background
    hover_color="#6d28d9",    # darker violet on hover
    ...
)
```

### Color reference for the current design

| Usage | Hex | Notes |
|---|---|---|
| Success / ready | `#2ecc71` | Green status text |
| In-progress | `"orange"` | CTK named color |
| Error | `"red"` | CTK named color |
| Idle | `"gray"` | CTK named color |
| Docs button | `#4dabf7` | Blue |
| Search button | `#2ecc71` | Green |
| Log utility buttons | `#2c2c2c` | Dark, intentional |
| CSV export button | `#2c6e49` | Forest green |
| JSON export button | `#1a4a6e` | Navy blue |

### Window size

In `BookmarkApp.__init__`:

```python
self.geometry("720x760")     # width × height in pixels
self.resizable(False, False)  # change to True, True to allow resizing
```

---

## Vault Dashboard Appearance

The HTML dashboard from `vault_builder.py` has its CSS inline in `generate_index_page`. The Archive Beautifier writes its CSS to a separate `style.css` - edit that file directly after generating an archive.

### Vault Builder dashboard tokens

| Property | Value | Element |
|---|---|---|
| Page background | `#121212` | `body` |
| Card background | `#1e1e1e` | `.user-container` |
| Card hover | `#383838` | `li:hover` |
| Accent blue | `#4dabf7` | User profile titles |
| Subdued text | `#aaaaaa` | Browser section headers |

### Archive Beautifier CSS variables

Edit `style.css` in the generated archive folder:

```css
:root {
    --bg-main:        #121212;
    --bg-surface:     #1e1e1e;
    --bg-card:        #2c2c2c;
    --bg-hover:       #383838;
    --text-primary:   #e0e0e0;
    --text-secondary: #aaaaaa;
    --accent:         #4dabf7;
    --border:         #333333;
}

html.light {
    --bg-main:        #f5f5f5;
    --bg-surface:     #ffffff;
    /* ... */
}
```

---

## Bookmark Merger: Search Query Customisation

The search engine in `core/search.py` uses AND logic with `-` exclusions. If you want to extend it (regex support, OR logic, date filtering), the core matching is in the `_matches` function:

```python
def _matches(entry: BookmarkEntry) -> bool:
    title = entry.title.lower()
    url   = entry.url.lower()
    haystack = ""
    if field in ("both", "title"):
        haystack += " " + title
    if field in ("both", "url"):
        haystack += " " + url
    for term in must_have:
        if term not in haystack:
            return False
    for term in must_not:
        if term in haystack:
            return False
    return True
```

Add a `date_from` / `date_to` filter by checking `entry.add_date` against a timestamp range before returning `True`.

For example, you could extend `_matches()` to ignore bookmarks older than a certain date by checking `entry.add_date` against a timestamp range:

- keep only bookmarks added after 2020,
- or filter a specific year when building an audit report.

These filters are applied before returning `True` from `_matches()`, so they integrate cleanly with the existing AND / `-` exclusion logic.

---

## Adding a New GUI Tab

This section is intended for developers who want to extend the GUI. Most users will never need these steps.

To add a sixth tool tab (for example, a `.jsonlz4` Firefox backup decoder):

### 1. Declare StringVars in `__init__`

```python
self.backup_src  = ctk.StringVar()
self.backup_dest = ctk.StringVar()
```

### 2. Add the tab name to `_build_ui`

```python
for name in ("1: Extractor", ..., "5: Merger", "6: Backup Decoder"):
    self._tabs.add(name)
```

### 3. Add a tip in `_TAB_TIPS`

```python
"6: Backup Decoder": "Tip: Select a .jsonlz4 file from Firefox's bookmarkbackups/ folder.",
```

### 4. Register traces in `_register_traces`

```python
pairs = [
    ...
    (self.backup_src, self.backup_dest, lambda: self.backup_status),
]
```

### 5. Build the tab layout

Follow the same pattern as `_build_extractor_tab`:
- `_field_row()` for path inputs
- `ctk.CTkLabel` assigned to `self.backup_status`
- `_action_buttons()` for the run + open pair
- `ToolTip()` on every interactive element

### 6. Write the background runner

```python
def _start_backup_decode(self) -> None:
    if not self.backup_src.get() or not self.backup_dest.get():
        return
    self.backup_status.configure(text="Decoding…", text_color="orange")
    self.backup_run_btn.configure(state="disabled")
    self._job_start("Backup Decoder")          # ← graceful exit integration
    threading.Thread(target=self._run_backup, daemon=True).start()

def _run_backup(self) -> None:
    try:
        # call your core function here
        ...
        self._q_status(self.backup_status, "Done - … bookmarks.", "#2ecc71")
        self._q_log("[Backup] Done.")
    except Exception as exc:
        self._q_status(self.backup_status, f"Error: {exc}", "red")
        self._q_log(f"[Backup] Error: {exc}")
    finally:
        self._job_done("Backup Decoder")       # ← graceful exit integration
        self._q_button(self.backup_run_btn, "normal")
```

The `_job_start` / `_job_done` pair integrates the new tab into the graceful exit system automatically. The close dialog will list it alongside other running operations.

### 7. Add paths to config persistence (optional)

```python
_CONFIG_KEYS = [
    ...,
    "backup_src", "backup_dest",
]
```

---

## Code Architecture Reference

### Data flow

```
retriever.py         copies raw files + writes manifest.json
    ↓
vault_builder.py     reads manifest → calls json_to_html / sqlite_to_html
bookmark_merger.py   reads manifest → parses all sources → merges / exports
search.py            reads manifest → parses all sources → filters and returns
archive_beautifier.py reads manifest → calls its own JSON/SQLite parsers → writes styled HTML
```

### Shared utilities (`core/utils.py`)

Currently contains one function: `get_human_date(unix_time: int) -> str`. To change the date format displayed everywhere, edit the `strftime` pattern here.

### Return value contract

All public functions return a dict with at minimum `status` and `warnings`. This consistency makes it trivial to chain them in scripts or build new front-ends.

### Exception philosophy

Typed exceptions for hard failures (caller can decide what to do). `warnings` list for recoverable per-item issues (permission denied on one folder, skipped unknown node type) so the operation continues and the caller gets a complete picture rather than an abrupt stop.
