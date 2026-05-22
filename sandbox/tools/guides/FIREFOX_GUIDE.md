# Firefox Portable - Setup and Usage Guide

## Download

Firefox Portable is distributed via PortableApps.com (official channel): 
https://portableapps.com/apps/internet/firefox_portable

Download the latest stable release. The file will be named: 
`FirefoxPortable_XXX_English.paf.exe`

## Installation

The `.paf.exe` file is a PortableApps installer, not the portable app itself. 
Run it once on the **host machine** to install Firefox Portable into the `tools\` folder:

1. Double-click `FirefoxPortable_XXX_English.paf.exe`
2. When prompted for the install location, browse to:
   ```text
   C:\Bookmark_Rescue\tools\Firefox\
   ```
3. Click Install and wait for it to finish

After installation the folder should contain `FirefoxPortable.exe` plus supporting folders (`App\`, `Data\`, `Other\`). Do not put the `.paf.exe` inside the `tools\` folder - run it from your Downloads folder and point it at the destination above.

## Markdown Viewer Extension (Offline Install)

The toolkit is designed to run offline. The Markdown Viewer extension by simov needs to be downloaded on the host and installed from a local file.

**Step 1 - Download the extension on the host**

Download the `.xpi` extension file directly from Mozilla's CDN:
```text
https://addons.mozilla.org/firefox/downloads/latest/markdown-viewer-webext/
```

Save it to `C:\Bookmark_Rescue\tools\Firefox\` and rename it to:
```text
markdown-viewer.xpi
```

**Step 2 - Install inside the sandbox**

This is a one-time step. Since Firefox Portable's profile lives in the host-backed `tools\Firefox\Data\profile\` folder, the extension installs once and persists across all sandbox sessions.

1. Launch Firefox Portable from the Desktop shortcut or directly from `Desktop\SandboxTools\Firefox\FirefoxPortable.exe`.
2. In the address bar type: `about:addons` and press Enter
3. Click the gear icon near the top right
4. Choose **Install Add-on From File...**
5. Browse to `Desktop\SandboxTools\Firefox\markdown-viewer.xpi`
6. Click Add when prompted

After installation, go to the extension settings and enable **Allow access to file URLs** so it can render local `.md` files.

> **Credit and more details**  
> Markdown rendering in this toolkit is provided by the open‑source [Markdown Viewer](https://github.com/simov/markdown-viewer) browser extension by **simov**. See the project README for full usage notes, advanced configuration and troubleshooting tips.

## Viewing Markdown Files

Once the extension is installed, drag any `.md` file onto the Firefox window or use File > Open File. The extension renders it with formatted headings, code blocks, and syntax highlighting.

Sandbox README files are accessible at:
```text
C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\SANDBOX_README.md
```
```text
C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\GUI_SANDBOX_README.md
```
```text
C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\CLI_SANDBOX_README.md
```

## Viewing HTML Output

Firefox is the recommended viewer for vault dashboard and beautifier output:
```text
C:\Bookmark_Rescue\2_Vault_Site\index.html
```
```text
C:\Bookmark_Rescue\Archive\index.html
```

Drag the file onto Firefox or use File > Open File.

## Notes

- The `.paf.exe` installer is only run once on the host, not inside the sandbox.
- Firefox settings and extensions persist across sandbox sessions because `tools\Firefox\Data\profile\` is host-backed.
- Firefox does not need reinstalling each session.
- The Markdown Viewer extension only needs to be installed once.
- For background and updates, see the Markdown Viewer project: [https://github.com/simov/markdown-viewer#table-of-contents](https://github.com/simov/markdown-viewer#table-of-contents)
