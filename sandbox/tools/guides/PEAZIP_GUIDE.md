# PeaZip - Setup and Usage Guide

## Download

PeaZip portable is available from the official site: 
https://peazip.github.io/

Click "Download PeaZip" and choose the **portable** build for Windows 64-bit. The file will be named: `peazip_portable-X.X.X.WIN64.zip`

## Placement

Extract **all contents** of the zip into:
```text
C:\Bookmark_Rescue\tools\PeaZip\
```

**Do not create a nested subfolder** - the folder should contain `peazip.exe` and its supporting files directly at the root.

## vs 7-Zip

Both PeaZip and 7-Zip are included in the sandbox toolkit:

| | PeaZip | 7-Zip |
|---|---|---|
| Type | Portable (no install) | Installed per session |
| Context menu | No (sandbox only) | Yes (after setup_tools.bat) |
| GUI | Full graphical manager | Minimal |
| Formats | 200+ formats | Common formats |

PeaZip is available immediately without running `setup_tools.bat`. Use it for browsing archives with a GUI. Use 7-Zip for context menu integration when right-clicking files in Explorer.

## Notes

- PeaZip portable saves settings in its own folder.
- No reinstall needed per session.
- Settings persist between sessions since `tools\` is host-backed.
