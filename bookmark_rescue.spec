# bookmark_rescue.spec
# ---------------------------------------------------------------------------
# PyInstaller spec for Bookmark Rescue Toolkit
#
# Usage:
#   pip install pyinstaller
#   pyinstaller bookmark_rescue.spec
#
# Or use the helper script which handles everything including post-build copy:
#   python build.py
#
# Output: dist/BookmarkRescue/BookmarkRescue.exe  (Windows)
#         dist/BookmarkRescue/BookmarkRescue       (macOS / Linux)
#
# The dist/BookmarkRescue/ folder is self-contained and portable.
# Zip it and distribute it as-is.
# ---------------------------------------------------------------------------

from pathlib import Path
import sys

# SPECPATH is provided by PyInstaller and always points to the directory
# containing this spec file, regardless of where PyInstaller is invoked from.
# Using it (rather than Path('.')) ensures icon lookup is correct even when
# running: pyinstaller path/to/bookmark_rescue.spec from another directory.
_SPEC_DIR = Path(SPECPATH)
_ICO      = _SPEC_DIR / "icon.ico"
_PNG      = _SPEC_DIR / "icon.png"

# Resolve the best available icon for the .exe file itself.
# Window icons (shown at runtime) are handled separately in gui.py.
if _ICO.exists():
    _EXE_ICON = str(_ICO)
elif _PNG.exists():
    _EXE_ICON = str(_PNG)
else:
    _EXE_ICON = None

block_cipher = None

# ---------------------------------------------------------------------------
# Core application and Python sources
# ---------------------------------------------------------------------------
a = Analysis(
    ['gui.py'],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=[
        # Bundle the customtkinter theme and asset files so the GUI renders
        # correctly without a Python installation on the target machine.
        # PyInstaller does not auto-detect these - they must be listed explicitly.
        ('core', 'core'),
    ],
    hiddenimports=[
        # Standard library modules that PyInstaller sometimes misses
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'sqlite3',
        'csv',
        'html.parser',
        'urllib.parse',
        'webbrowser',
        # customtkinter internals
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.widgets',
        'customtkinter.windows.widgets.theme',
    ],
    # Tell PyInstaller to collect all customtkinter data (themes, fonts, images)
    collect_all=['customtkinter'],
    hookspath=[],
    runtime_hooks=[],
    # Strip heavy scientific packages if accidentally present in the environment.
    # This keeps the bundle lean.
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'Pillow',
              'IPython', 'jupyter', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # one-directory mode (faster launch, better AV behaviour)
    name='BookmarkRescue',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                # compress with UPX if available (reduces size ~30%)
    console=False,           # no terminal window on launch
    # Use the pre-resolved icon path (set at top of spec file).
    # None means PyInstaller uses its default icon -- no error.
    icon=_EXE_ICON,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    # This is the folder name inside dist/
    name='Bookmark-Rescue-Toolkit',
)
