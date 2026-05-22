# Notepad++ - Setup and Usage Guide

## Download

Notepad++ provides an official portable build: 
https://notepad-plus-plus.org/downloads/

Click the latest release, scroll to "Download 64-bit x64", and download the file named `npp.X.X.X.portable.x64.zip`.

## Placement

Extract **all contents** of the zip into:
```text
C:\Bookmark_Rescue\tools\Notepad++\
```

Do not create a nested subfolder - the folder should contain `notepad++.exe` and its supporting files directly at the root.

## Useful Plugins

Notepad++ supports plugins for Markdown preview and syntax highlighting.    
Install via Plugins > Plugins Admin inside Notepad++:

- **MarkdownPanel** - live preview panel for `.md` files
- **MarkdownViewer++** - *on-the-fly markdown file viewer*
- **NppExport** - export files to HTML or PDF

## Opening Files

Notepad++ portable does not add itself to the Windows right-click context menu. Open files by dragging them onto the Notepad++ window, or use File > Open from within Notepad++.

To open a file from the CMD prompt:
```text
C:\Users\WDAGUtilityAccount\Desktop\SandboxTools\Notepad++\notepad++.exe "C:\path\to\file.txt"
```

Useful for viewing generated output files:
- `C:\Bookmark_Rescue\3_Merged\bookmarks.csv`
- `C:\Bookmark_Rescue\3_Merged\bookmarks.json`
- `C:\Bookmark_Rescue\2_Vault_Site\index.html`

## Notes

- Notepad++ portable saves settings in its own folder.
- Settings persist between sessions since `tools\` is host-backed.
- No reinstall needed per session.
