# ShareX

Place the ShareX portable contents here after completing the one-time setup below.

## Quick Start

**Step 1 - Confirm the pre-configured personal folder is in place**

The repo includes a pre-configured `ApplicationConfig.json` that must exist before ShareX runs for the first time:

```text
C:\Bookmark_Rescue\tools\ShareX\ShareX\ApplicationConfig.json
```

After cloning the repo this folder and file should already be here.  
If not, create the `ShareX\ShareX\` folder manually and copy the `ApplicationConfig.json` from the repo into it.

**Step 2 - Download ShareX portable**

Official GitHub releases page: 
https://github.com/ShareX/ShareX/releases

Under Assets, download:
```text
ShareX-X.X.X-portable.zip
```

**Step 3 - Extract the zip into this folder**

Extract all contents directly into:
```text
C:\Bookmark_Rescue\tools\ShareX\
```

The result should look like:
```text
tools\ShareX\
    ShareX.exe              <- from zip
    (other app files)       <- from zip
    ShareX\                 <- was already here (from repo)
        ApplicationConfig.json
```

ShareX.exe should be at the root of `tools\ShareX\` - not nested in a subfolder.

**Step 4 - Launch ShareX**

On first run ShareX reads the pre-configured `ApplicationConfig.json` and saves screenshots to `Desktop\Screenshots\YYYY\MM\` automatically.

## Notes

- The portable zip does not include the personal `ShareX\ShareX\` folder - ShareX creates it on first run. Pre-placing our config there before that first run is what makes the screenshot path work correctly.
- Portable app files are not committed to the repo - only `ShareX\ShareX\ApplicationConfig.json` is.
- Settings persist across sandbox sessions since `ShareX\ShareX\` is host-backed.
- `AutoCheckUpdate` is disabled to suppress network prompts on launch.

## Further Reading

- [SHAREX_GUIDE.md](../guides/SHAREX_GUIDE.md) - full setup and usage guide
- [TOOLS_README.md](../TOOLS_README.md) - overview of all sandbox tools
