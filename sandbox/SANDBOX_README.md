# BRT Sandbox Environments

> **Optional contributor tools**
> 
> These sandboxes are for maintainers and contributors who need consistent
> screenshots, demo data, or an isolated testing environment.
> They are **not required** to use Bookmark Rescue Toolkit.

Two self-contained Windows Sandbox environments for the Bookmark Rescue Toolkit,
each serving a different purpose but sharing the same mock data, workspace
structure, and host folder layout.

## At a Glance

| | GUI Sandbox | CLI Sandbox |
|---|---|---|
| **Purpose** | Screenshot the portable `.exe` GUI | Screenshot CLI tool output in Command Prompt |
| **Runs** | `BookmarkRescue.exe` (portable build) | Python source via `python -m core.*` & Portable `.exe`|
| **Networking** | Disabled | Disabled (optional networking-enabled variant available) |
| **Python required** | No | Yes - installed from local file |
| **Setup time** | ~30 sec | ~90 sec (local Python install) |
| **Launcher** | `Launch_GUI_Sandbox.bat` | `Launch_CLI_Sandbox.bat` |
| **Guide** | [GUI_SANDBOX_README.md](GUI_SANDBOX_README.md) | [CLI_SANDBOX_README.md](CLI_SANDBOX_README.md) |

---

## Shared Setup

Both sandboxes use the same host folder layout and mock data. Set these up
once and both environments are ready.

### Windows Sandbox

Must be enabled before either sandbox can run:

```
OptionalFeatures.exe -> tick "Windows Sandbox" -> OK -> restart
```

Verify after restart:
```
where WindowsSandbox.exe
```

### Two Separate Root Folders

> `C:\Bookmark-Rescue-Toolkit\` (hyphen) - the repo and portable app
> `C:\Bookmark_Rescue\` (underscore) - the screenshot workspace

```
C:\Bookmark-Rescue-Toolkit\          <- repo root (hyphen, matches GitHub name)
    dist\
        Bookmark-Rescue-Toolkit\
            BookmarkRescue.exe        <- required by GUI Sandbox

C:\Bookmark_Rescue\                   <- shared workspace (underscore, matches docs)
    Sandbox\                          <- all sandbox files live here
    Screenshots\                      <- shot output, live-syncs to host
    Windows.old\                      <- shared mock data (generated once)
        Users\
            Alex\    <- Chrome, Edge, Brave, Firefox
            Jordan\  <- Chrome, Brave, Firefox, Opera
```

### Mock Data

The mock data at `C:\Bookmark_Rescue\Windows.old\` is shared between both
sandboxes. Generate it once by running the GUI sandbox launcher - it creates
the data on the host before opening the sandbox:

```
C:\Bookmark_Rescue\Sandbox\Launch_GUI_Sandbox.bat
```

You can close the sandbox window immediately after it opens if you only needed
the mock data for the CLI sandbox.

| User | Browsers | Bookmark categories |
|---|---|---|
| Alex | Chrome, Edge, Brave, Firefox | Dev tools, GitHub, Stack Overflow, privacy, learning |
| Jordan | Chrome, Brave, Firefox, Opera | Shopping, news, streaming, gaming, finance, recipes |

~65 bookmarks per user. All URLs point to public websites only.
No personal data from any real installation is included.

To regenerate mock data:
```
rmdir /s /q C:\Bookmark_Rescue\Windows.old
```
Then re-run `Launch_GUI_Sandbox.bat`.

### Inside Both Sandboxes

The workspace mirrors the documentation paths exactly:

```
C:\Windows.old\                       <- mock source drive (Tab 1 field)
C:\Bookmark_Rescue\
    1_Raw_Extracted_Data\             <- Tab 1 output
    2_Vault_Site\                     <- Tab 4 output
    3_Merged\                         <- Tab 5 output
```

---

## Shared Troubleshooting

**Security warning when double-clicking a launcher**:  
Windows tags files extracted from a zip with a security zone marker. Right-click the `.bat` file > Properties > tick Unblock > OK. One-time fix per file. Files cloned directly via git are not affected.

**Windows Sandbox not available**:  
Run `OptionalFeatures.exe`, tick "Windows Sandbox", click OK and restart.
Confirm with `where WindowsSandbox.exe` after restarting.

**Mock data not found**:  
Run `Launch_GUI_Sandbox.bat` on the host - it generates
`C:\Bookmark_Rescue\Windows.old\` which both sandboxes share.

**Screenshots not appearing on host**:  
Save to `C:\Users\WDAGUtilityAccount\Desktop\Screenshots\` inside the sandbox.
That folder maps directly to `C:\Bookmark_Rescue\Screenshots\` on the host
and files sync instantly.

**Win+Shift+S does not save**:  
This shortcut only copies to clipboard inside Windows Sandbox. Use
Snipping Tool directly (search it in the Start menu) and use File > Save As.

---

## File Placement

All files live in `C:\Bookmark_Rescue\Sandbox\`:

```
C:\Bookmark_Rescue\Sandbox\
    BRT_CLI_Sandbox.wsb              <- CLI sandbox config (offline)
    BRT_CLI_Sandbox_Net.wsb          <- CLI sandbox config (networking on)
    cli_launcher_inside.bat          <- spawns CMD window inside CLI sandbox
    CLI_SANDBOX_README.md            <- CLI sandbox guide
    cli_sandbox_startup.bat          <- CLI session script
    generate_mock_data.py            <- mock data generator (shared)
    GUI_SANDBOX_README.md            <- GUI sandbox guide
    GUI_Sandbox.wsb                  <- GUI sandbox config
    Launch_CLI_Sandbox.bat           <- CLI sandbox launcher
    Launch_GUI_Sandbox.bat           <- GUI sandbox launcher
    SANDBOX_README.md                <- this file
    sandbox_startup.bat              <- sandbox startup script (shared)
    python_installer\
        python-3.12.10-amd64.exe     <- required by CLI sandbox, not committed
```

---

## Adding to the Repo

The `sandbox/` folder is excluded from the dist build automatically since it
is not listed in `ASSETS_TO_COPY` in `build.py`. Add to `.gitignore`:

```gitignore
# Sandbox generated data and local tools
sandbox/Windows.old/
sandbox/python_installer/
```

The `python_installer\` subfolder should not be committed. Add it locally
after cloning by downloading the Python 3.12 64-bit installer from
[python.org](https://www.python.org/downloads/release/python-31210) and placing it there.
