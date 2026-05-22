# Building a Portable .exe

This guide covers building Bookmark Rescue Toolkit into a self-contained, portable Windows application that requires no Python installation on the target machine.

> If you prefer not to build from source, you can download the latest
> `BookmarkRescue_vX.Y.Z.zip` from the project's [GitHub Releases page](https://github.com/webshoppe/bookmark-rescue-toolkit/releases) and skip directly to extraction and recovery.

## Table of contents

- [How it works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Quick build](#quick-build)
- [Output](#output)
- [Build size](#build-size)
- [Antivirus false positives](#antivirus-false-positives)
- [Customising the .exe icon](#customising-the-exe-icon)
- [Making changes and rebuilding](#making-changes-and-rebuilding)
- [Advanced: Editing the spec file](#advanced-editing-the-spec-file)
- [Versioning](#versioning)
- [Distributing](#distributing)

---

## How It Works

The build uses [PyInstaller](https://pyinstaller.org) in **one-directory mode**; it produces a folder named `Bookmark-Rescue-Toolkit` containing the executable `BookmarkRescue.exe` and its support files along with a versioned zip file. *Place your `icon.ico` and `icon.png` in the repository root before building so they are automatically included.* The entire folder is portable: copy it anywhere, zip it, put it on a USB drive. No installer, no registry entries, no admin rights needed to run it.

```
Bookmark-Rescue-Toolkit/
    BookmarkRescue.exe     <- launch this
    docs/
        GUI_WALKTHROUGH.md
        MANUAL_TOOLS.md
        CUSTOMIZATION.md
    README.md
    LICENSE
    icon.ico               <- optional, user-replaceable
    icon.png               <- optional, user-replaceable
    _internal/             <- PyInstaller internals, leave untouched
```

The `docs/` folder and `README.md` are copied next to the `.exe` so the in-app **View Docs** button works out of the box. The icon files are also copied so users can swap them without rebuilding.

The `.zip` archive created with `--zip` will be named `BookmarkRescue_vX.Y.Z.zip`.

> **Note:** The `assets/screenshots/` folder is intentionally excluded from the portable build. It exists for repository documentation only and adds no value to end users.

---

## Prerequisites

- Python **3.10+** (developed and tested on 3.12)
- Your virtual environment must be active
- Build from the **repository root** (the folder containing `gui.py`)

---

## Quick Build

**Setup and activate your environment first, run:**

- **Windows**
```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
```

- **macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Install dependencies**

```bash
pip install -r requirements.txt
```

> **pip update notice:**  
> After running pip you may see a message like `A new release of pip is available: X.X -> X.X`. This is informational only and can be safely ignored - pip works correctly without upgrading.

***When you are finished, deactivate the virtual environment with:***
```bash
deactivate
```

> **Tip:** Always deactivate your virtual environment when finished (`deactivate`) to avoid accidental use of the wrong Python environment.

### Build the executable
```bash
python build.py
```

### Build and create a distributable .zip in one step
```bash
python build.py --zip
```

### Clean previous build artifacts, then build fresh
```bash
python build.py --clean
```

### All three at once
```bash
python build.py --clean --zip
```

The first run will offer to install PyInstaller if it is not already present. If you prefer to install it manually:

```bash
pip install pyinstaller
```

---

## Output

After a successful build:

```
dist/
    Bookmark-Rescue-Toolkit/           <- the portable application folder
        BookmarkRescue.exe
        docs/
        README.md
        LICENSE
        _internal/
    BookmarkRescue.zip_vX.Y.Z.zip     <- only created with --zip flag
```

> The `.zip` archive created with `--zip` will be named `BookmarkRescue_vX.Y.Z.zip`.

Build time is typically 60-120 seconds on the first run. Subsequent builds are faster because PyInstaller caches intermediate results in `build/`.

> **Note:** The `assets/screenshots/` folder is intentionally excluded from the portable build. It exists for repository documentation only and adds no value to end users.

---

## Build Size

Expect the uncompressed folder to be around **80-120 MB** due to the Python runtime and tkinter libraries being bundled. The `.zip` archive compresses to roughly **40-60 MB**.

UPX compression is enabled by default in the spec file and reduces binary sizes by about 30%. UPX is optional - if it is not installed the build still completes, just slightly larger. Install it from [upx.github.io](https://upx.github.io) and ensure it is on your PATH.

---

## Antivirus False Positives

PyInstaller-built executables are occasionally flagged by antivirus software because of the way Python code gets packed into a PE binary. This is a known issue with PyInstaller broadly, not specific to this project.  

VirusTotal results for the release build: 2/71 detections (Arctic Wolf, Yandex).  
  - Both are heuristic false positives. The Yandex detection is literally labelled `Riskware.PyInstaller` - it is flagging the bootloader, not any code in the toolkit.  
  - All major vendors (Windows Defender, Kaspersky, Bitdefender, ESET, Malwarebytes) return clean.  
  
A result under 5/71 from reputable vendors is considered clean by the security community.

If you rebuild from source and want to verify your own build:

- Submit the file to [VirusTotal](https://www.virustotal.com) to check the consensus across multiple engines
- Most security scanners clear PyInstaller-built apps within days of initial false-positive reports
- One-directory mode (which this project uses) triggers false positives less often than one-file mode because the executable does not self-extract at runtime

---

## Customising the .exe Icon

The executable icon (the `.exe` file's icon in Explorer, taskbar, and Alt+Tab) is separate from the window icon.

To set a custom `.exe` icon:

1. Place `icon.ico` in the repository root
   > The build script will automatically copy `icon.ico` and `icon.png` (if present) into the final `Bookmark-Rescue-Toolkit` folder.
2. The `bookmark_rescue.spec` file picks it up automatically
3. Rebuild with `python build.py`

The spec file contains:
```python
icon='icon.ico' if Path('icon.ico').exists() else None,
```

Recommended `.ico` sizes: 16x16, 32x32, 48x48, 256x256 -> all embedded in one `.ico` file.

---

## Making Changes and Rebuilding

After changing Python source files, run `python build.py` again. You do not need `--clean` for code changes alone.

Use `--clean` when:
- You have changed the spec file
- You have added or removed files from `datas` in the spec
- You encounter unexplained build errors

---

## Advanced: Editing the Spec File

`bookmark_rescue.spec` is a regular Python file. The most common reasons to edit it:

**Adding a new data file to the bundle:**
```python
datas=[
    ('core', 'core'),
    ('assets/my_file.dat', 'assets'),   # add this
],
```

**Adding a hidden import for a new dependency:**
```python
hiddenimports=[
    ...,
    'my_new_module',
],
```

**Disabling UPX** (if it causes issues on your machine):
```python
upx=False,
```

---

## Versioning

This project follows semantic versioning (MAJOR.MINOR.PATCH).

- **MAJOR**: Breaking changes (rare)
- **MINOR**: New features or significant improvements
- **PATCH**: Bug fixes and small updates

Before building a release:

1. Update the version number in `core/version.py` (look for `__version__ = "X.Y.Z"`).
2. Update `CHANGELOG.md` for the new version, if present.
3. Run `python build.py --clean --zip`.

When publishing on GitHub, use a tag like `vX.Y.Z` that matches the version in `core/version.py`.  
The build script will automatically include the version in the output zip filename (`BookmarkRescue_vX.Y.Z.zip`).

---

## Distributing

The `dist/Bookmark-Rescue-Toolkit/` folder is fully self-contained. To distribute it:

1. Run `python build.py --zip`.
2. Upload `dist/BookmarkRescue_vX.Y.Z.zip` to the project's
   [GitHub Releases page](https://github.com/webshoppe/bookmark-rescue-toolkit/releases).
3. Users download the zip, extract it anywhere, and run `BookmarkRescue.exe`.

No installer, no admin rights, and no Python installation are required on the target machine.
