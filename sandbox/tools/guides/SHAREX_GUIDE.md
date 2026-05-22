# ShareX - Setup and Usage Guide

## Download

ShareX portable is available from the official GitHub releases page:  
https://github.com/ShareX/ShareX/releases

Under Assets, download the file named: 

```text
ShareX-X.X.X-portable.zip
```

**Do not use the standard `-setup.exe` installer.**

## Folder Structure

The ShareX portable zip contains only the application files - `ShareX.exe` and its supporting files. There is no personal folder in the zip.

ShareX creates its personal data folder (`ShareX\ShareX\`) automatically on first run. In this toolkit we **pre-create** that folder and place our `ApplicationConfig.json` inside it before the first launch, so ShareX picks up the pre-configured screenshot paths instead of writing its own defaults.

```text
tools\ShareX\
    ShareX.exe                  <- from the portable zip
    (other app files)           <- from the portable zip
    ShareX\                     <- created manually before first run
        ApplicationConfig.json  <- pre-configured, committed to repo
```

The `ShareX\ShareX\` folder is host-backed so settings, screenshot history, and the config persist across sandbox sessions automatically.

## Setup (one-time on host)

The personal folder and config must exist before `ShareX.exe` runs for the first time. The order matters.

### Step 1 - Confirm the pre-configured folder is in place

The repo already includes:

```text
C:\Bookmark_Rescue\tools\ShareX\ShareX\ApplicationConfig.json
```

If that path does not exist on your host (for example, after a fresh clone), create the `ShareX\ShareX\` folder manually and copy `ApplicationConfig.json` into it before proceeding.

### Step 2 - Extract the portable zip

Extract **all contents** of `ShareX-X.X.X-portable.zip` directly into:

```text
C:\Bookmark_Rescue\tools\ShareX\
```

Do not create a nested subfolder - `ShareX.exe` should sit at the root of `tools\ShareX\` alongside the pre-existing `ShareX\` personal folder.

### Step 3 - Launch ShareX

On first launch ShareX finds the existing `ShareX\ShareX\` folder, reads `ApplicationConfig.json`, and applies the configured screenshot path and year/month subfolder pattern automatically. No further configuration needed.

## Screenshot Save Location

With the pre-configured `ApplicationConfig.json` in place, screenshots save to:

```text
Desktop\Screenshots\YYYY\MM\
```

and sync instantly to:

```text
C:\Bookmark_Rescue\Screenshots\
```

on the host.

If screenshots land in `tools\ShareX\ShareX\Screenshots\` instead, the config was not in place before first launch. Fix it manually in ~30 seconds:

1. Open ShareX > **Application settings > Paths**.
2. Tick **Use custom screenshot folder**.
3. Set the path to:

   ```text
   C:\Users\WDAGUtilityAccount\Desktop\Screenshots
   ```

This setting is then written back to `ApplicationConfig.json` and persists permanently since the personal folder is host-backed.

## Taking Screenshots

| Action            | Method                                   |
|-------------------|------------------------------------------|
| Capture region    | ShareX tray icon > Capture > Region      |
| Capture window    | ShareX tray icon > Capture > Window      |
| Capture fullscreen| ShareX tray icon > Capture > Screen      |

ShareX auto-saves immediately after capture with no save dialog, which is ideal for step-by-step GUI and CLI screenshots.

## Notes

- The `ShareX\ShareX\` personal folder is host-backed - settings, history, and the configured screenshot path persist across sandbox sessions automatically.
- `AutoCheckUpdate` is disabled in the pre-configured `ApplicationConfig.json` to suppress the network connection prompt on launch.
- ShareX does not need reinstalling per session - it is a portable app.
