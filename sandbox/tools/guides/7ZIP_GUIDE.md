# 7-Zip - Setup and Usage Guide

## Download

7-Zip is available from the official site: 
https://www.7-zip.org/download.html

Choose the **Windows x64 executable installer** row:
```text
7z2409-x64.exe   (or the current stable release)
```

Direct link to current stable: 
https://www.7-zip.org/a/7z2409-x64.exe

## Placement

Place the downloaded installer at: 
```text
C:\Bookmark_Rescue\tools\7zip_installer\7z2409-x64.exe
```

The filename does not need to match exactly - `setup_tools.bat` finds any `.exe` in the `7zip_installer\` folder automatically.

## Installation

7-Zip must be installed each sandbox session since the sandbox resets on close. `setup_tools.bat` handles this automatically on each run.

After installation, 7-Zip integrates with Windows Explorer context menus:
```text
Right-click any file or archive > 7-Zip > Extract here
```

## Why Reinstall Each Session?

Windows Sandbox discards all changes on close, including installed software. 7-Zip registers itself with the Windows shell (context menu, file associations) which requires a proper install. PeaZip portable in `tools\PeaZip\` provides archive browsing without reinstalling and is available immediately.

## Notes

- Run `setup_tools.bat` at the start of each sandbox session
- The installer binary is in `.gitignore` and is never committed to the repo
