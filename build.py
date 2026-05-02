"""
build.py -- Bookmark Rescue Toolkit build helper
=================================================
Runs PyInstaller and assembles the final portable distribution folder.

Usage:
    python build.py            # build the .exe distribution
    python build.py --zip      # also create a .zip archive for distribution
    python build.py --clean    # remove build/ and dist/ then build fresh

What this script does:
    1. Checks that PyInstaller is installed (and offers to install it)
    2. Runs PyInstaller with the bookmark_rescue.spec file
    3. Copies docs/, README.md, and LICENSE into dist/BookmarkRescue/
       so they sit next to the .exe and are readable by the app
    4. Copies icon.ico / icon.png if present (so the window icon works)
    5. Optionally creates a distributable .zip archive

Output layout:
    dist/
        BookmarkRescue/
            BookmarkRescue.exe     <- run this
            docs/
                GUI_WALKTHROUGH.md
                MANUAL_TOOLS.md
                CUSTOMIZATION.md
            README.md
            LICENSE
            icon.ico               <- if present in repo root
            icon.png               <- if present in repo root
            _internal/             <- PyInstaller internals, do not touch
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from core.version import __version__

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE      = Path(__file__).parent

# Distribution folder name (matches repo style with hyphen)
DIST_DIR  = HERE / "dist" / "Bookmark-Rescue-Toolkit"

# Build artifacts
BUILD_DIR = HERE / "build"
SPEC_FILE = HERE / "bookmark_rescue.spec"

# Files / folders copied next to the .exe after the PyInstaller build
# assets/ is intentionally excluded from the dist build.
# Screenshots live in the repo for documentation purposes only.
ASSETS_TO_COPY = [
    ("README.md", "README.md"),
    ("LICENSE",   "LICENSE"),
    ("docs",      "docs"),
    # ("assets",  "assets"),  <- excluded: repo/docs use only
]
OPTIONAL_ICONS = ["icon.ico", "icon.png"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd: list[str], check: bool = True) -> int:
    print(f"\n>>> {' '.join(cmd)}\n")
    result = subprocess.run(cmd, check=False)
    if check and result.returncode != 0:
        print(f"\nCommand failed with exit code {result.returncode}.")
        sys.exit(result.returncode)
    return result.returncode


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed.")
        answer = input("Install it now? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        else:
            print("Cannot build without PyInstaller. Exiting.")
            sys.exit(1)


def clean_previous() -> None:
    for folder in (BUILD_DIR, HERE / "dist"):
        if folder.exists():
            print(f"Removing {folder}...")
            shutil.rmtree(folder)


def copy_assets() -> None:
    """Copy docs, README, LICENSE, and optional icons next to the .exe."""
    print("\nCopying assets into dist/BookmarkRescue/...")
    for src_name, dest_name in ASSETS_TO_COPY:
        src  = HERE / src_name
        dest = DIST_DIR / dest_name
        if not src.exists():
            print(f"  SKIP (not found): {src_name}")
            continue
        if src.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"  Copied folder: {src_name}/")
        else:
            shutil.copy2(src, dest)
            print(f"  Copied file:   {src_name}")

    for icon_name in OPTIONAL_ICONS:
        icon_src = HERE / icon_name
        if icon_src.exists():
            shutil.copy2(icon_src, DIST_DIR / icon_name)
            print(f"  Copied icon:   {icon_name}")


def make_zip() -> None:
    """Zip the dist/BookmarkRescue/ folder into dist/BookmarkRescue.zip."""
    zip_path = HERE / "dist" / f"BookmarkRescue_v{__version__}.zip"
    print(f"\nCreating {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in DIST_DIR.rglob("*"):
            zf.write(file, file.relative_to(HERE / "dist"))
    size_mb = zip_path.stat().st_size / 1_048_576
    print(f"Archive ready: {zip_path}  ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Bookmark Rescue Toolkit portable .exe.",
    )
    parser.add_argument("--zip",   action="store_true",
                        help="Create a .zip archive after building")
    parser.add_argument("--clean", action="store_true",
                        help="Remove previous build artifacts before building")
    args = parser.parse_args()

    print(f"=== Bookmark Rescue Toolkit Build Script  v{__version__} ===\n")

    ensure_pyinstaller()

    if args.clean:
        clean_previous()

    if not SPEC_FILE.exists():
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        print("Make sure you run this script from the repository root.")
        sys.exit(1)

    # Run PyInstaller
    run([sys.executable, "-m", "PyInstaller", str(SPEC_FILE), "--noconfirm"])

    if not DIST_DIR.exists():
        print(f"\nERROR: Expected output folder not found: {DIST_DIR}")
        print("Check the PyInstaller output above for errors.")
        sys.exit(1)

    copy_assets()

    if args.zip:
        make_zip()

    exe_name = "BookmarkRescue.exe" if sys.platform == "win32" else "BookmarkRescue"
    print(f"\n=== Build complete ===")
    print(f"Executable: {DIST_DIR / exe_name}")
    print(f"Portable folder: {DIST_DIR}")
    if args.zip:
        print(f"Distribution archive: {HERE / 'dist' / f'BookmarkRescue_v{__version__}.zip'}")


if __name__ == "__main__":
    main()
