# BRT Sandbox Tools - Overview

A curated set of portable tools available inside both BRT sandbox environments.  
All tools live in `C:\Bookmark_Rescue\tools\` on the host and map directly to `Desktop\SandboxTools\` inside either sandbox.

> These tools are optional and not required to use Bookmark Rescue Toolkit.  
> They exist to support screenshot sessions, content viewing, and contributor workflows.

> **Important:**  
> The BRT Sandbox Tools folder is a live mapped folder. Any files created, edited, or deleted inside the sandbox are immediately reflected on the host at `C:\Bookmark_Rescue\tools\`. Changes persist after the sandbox closes.

> **Repo vs host location:**  
> In the repository this folder lives at `sandbox/tools/` for organizational purposes. On your host machine it must be at `C:\Bookmark_Rescue\tools\` - that is the path the sandbox WSB files map to. After cloning, copy the `tools/` folder from `sandbox/tools/` to `C:\Bookmark_Rescue\tools\` before running either sandbox.

---

## Quick Start

1. Download and place each portable tool in its subfolder (see guides below)
2. Place the 7-Zip installer in `7zip_installer\` (see [`7zip_installer\README.md`](7zip_installer/README.md))
3. Run Firefox Portable installer once on the host (see [`guides\FIREFOX_GUIDE.md`](guides/FIREFOX_GUIDE.md))
4. On the **host**, launch the sandbox and wait for the desktop to fully load
5. Double-click `setup_tools.bat` from `Desktop\SandboxTools\` inside the sandbox
6. Shortcuts appear on the Desktop automatically

**When to run `setup_tools.bat`:**

- Once per sandbox session - 7-Zip must be reinstalled each session because the sandbox discards all installed software on close.
- Portable tools (Firefox, Notepad++, ShareX, SumatraPDF, PeaZip) are ready immediately without running the script - they live in the host-backed tools folder and are available the moment the sandbox loads.
- Re-run anytime to recreate Desktop shortcuts if they were lost.

---

## Tools

| Tool             | Folder           | Purpose                                  | Type                   |
|------------------|------------------|------------------------------------------|------------------------|
| 7-Zip            | `7zip_installer\`| Archive extraction with context menu     | Installed per session  |
| Firefox Portable | `Firefox\`       | HTML output viewer, Markdown viewer      | Portable               |
| Notepad++        | `Notepad++\`     | Code and file viewer / editor           | Portable               |
| PeaZip           | `PeaZip\`        | Archive browser (no install needed)      | Portable               |
| ShareX           | `ShareX\`        | Screenshot capture with auto-save        | Portable               |
| SumatraPDF       | `SumatraPDF\`    | PDF and document viewer                  | Portable               |

---

## Folder Structure
```text
C:\Bookmark_Rescue\tools\       <- copy from repo clone: Bookmark-Rescue-Toolkit/sandbox/tools
    7zip_installer\             <- place 7-Zip .exe installer here
        README.md
    Firefox\                    <- run paf.exe installer on host, point here
        README.md               <- download and setup instructions
    guides\                     <- individual setup and usage guides
        7ZIP_GUIDE.md
        FIREFOX_GUIDE.md
        NOTEPAD_GUIDE.md
        PEAZIP_GUIDE.md
        SHAREX_GUIDE.md
        SUMATRA_GUIDE.md
        JOPLIN_PLACEHOLDER.md
    Notepad++\                  <- extract portable zip contents here
        README.md
    Notes\                      <- persistent notes (host-backed, persists across sessions)
        .gitkeep
    PeaZip\                     <- extract portable zip contents here
        README.md
    ShareX\                     <- extract portable zip contents here
        README.md               <- setup order instructions
        ShareX\                 <- personal folder (committed, pre-configured)
            ApplicationConfig.json
    SumatraPDF\                 <- place renamed SumatraPDF.exe here
        README.md
    setup_tools.bat             <- run once per session inside sandbox
    TOOLS_README.md             <- this file
```

---

## Notes Folder

`tools\Notes\` is host-backed - anything saved there persists across sandbox sessions and is accessible from the host at `C:\Bookmark_Rescue\tools\Notes\`. Use it for session notes, reference snippets, or working drafts.

---

## Individual Guides

Detailed download, setup, and usage instructions for each tool:

- [7-Zip](guides/7ZIP_GUIDE.md)
- [Firefox + Markdown Viewer](guides/FIREFOX_GUIDE.md)
- [Notepad++](guides/NOTEPAD_GUIDE.md)
- [PeaZip](guides/PEAZIP_GUIDE.md)
- [ShareX](guides/SHAREX_GUIDE.md)
- [SumatraPDF](guides/SUMATRA_GUIDE.md)
- [Joplin](guides/JOPLIN_PLACEHOLDER.md) *(planned - not yet available)*

---

## Image Viewing in the Sandbox

Windows Photo Viewer is not available in Windows Sandbox and cannot be re-enabled. For image previews inside the sandbox:

- **ShareX** includes a built-in viewer for captured screenshots
- **Microsoft Paint** is always available (search in Start menu)
- **SumatraPDF** opens common image formats (PNG, JPG, BMP, TIFF)
- For anything more, view images from the host - they sync instantly via `C:\Bookmark_Rescue\Screenshots\`

---

## Adding to the Repo

The `tools\` folder structure (READMEs and config files) is committed to the repo.  
Portable binaries and installers are not - add them locally after cloning.

Items excluded via `.gitignore`:
```
sandbox/tools/7zip_installer/*.exe
sandbox/tools/Firefox/
sandbox/tools/Notepad++/
sandbox/tools/SumatraPDF/
sandbox/tools/ShareX/*.exe
sandbox/tools/PeaZip/
```
