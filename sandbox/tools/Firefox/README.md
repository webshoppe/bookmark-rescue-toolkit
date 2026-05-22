# Firefox

Place the Firefox Portable installation here before running `setup_tools.bat`.

## Download and Install

Firefox Portable is distributed via PortableApps.com: 
https://portableapps.com/apps/internet/firefox_portable

Download the latest stable release (`FirefoxPortable_XXX_English.paf.exe`).

The `.paf.exe` is a PortableApps installer - run it once on the **host machine** and point it at this folder:
```text
C:\Bookmark_Rescue\tools\Firefox\
```

After installation this folder should contain `FirefoxPortable.exe` and supporting folders (`App\`, `Data\`, `Other\`).

## Markdown Viewer Extension

Download the `.xpi` file on the host and place it here for offline installation: 
https://addons.mozilla.org/firefox/downloads/latest/markdown-viewer-webext/

Rename it to `markdown-viewer.xpi` for easy reference.

## Notes

- The `.paf.exe` installer is run on the host, not inside the sandbox.
- Portable contents and installed profile are not committed to the repo.
- Extension only needs installing once - the profile is host-backed and persists.
- Read more about the Markdown Viewer / Browser Extension: [https://github.com/simov/markdown-viewer#table-of-contents](https://github.com/simov/markdown-viewer#table-of-contents)

## Further Reading

- [FIREFOX_GUIDE.md](../guides/FIREFOX_GUIDE.md)
- [TOOLS_README.md](../TOOLS_README.md)
