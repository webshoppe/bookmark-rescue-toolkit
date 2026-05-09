# BRT CLI Sandbox

> **Optional contributor tool**
> 
> This sandbox is for maintainers and contributors who need consistent screenshots or demo data.  
> It is **not required** to use Bookmark Rescue Toolkit.

A Windows Sandbox environment that installs Python from a local installer, loads the BRT source repo, and runs each CLI engine in a styled Command Prompt with pauses between commands for clean screenshots.

It also includes the portable GUI, so you can demo both the CLI tools and `BookmarkRescue.exe` in a single isolated session.

For an overview of both sandbox environments and shared setup, see
[SANDBOX_README.md](SANDBOX_README.md).

> **Who is this for?**
> 
> - Maintainers capturing consistent CLI screenshots for docs or release notes  
> - Contributors testing BRT's CLI tools in an isolated, repeatable environment  
> - Anyone wanting a disposable Windows VM with the repo, mock data, and Python pre‑wired

## Table of contents

- [How It Differs from the GUI Sandbox](#how-it-differs-from-the-gui-sandbox)
- [File Placement](#file-placement)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
   - [Step 1 - Run the launcher](#step-1---run-the-launcher)
   - [Step 2 - Wait for setup](#step-2---wait-for-setup-90-seconds)
   - [Step 3 - Screenshot each command](#step-3---screenshot-each-command)
   - [Step 4 - Commands in sequence](#step-4---commands-in-sequence)
   - [Step 5 - Free exploration (optional)](#step-5---free-exploration-optional)
   - [Step 6 - Close the sandbox](#step-6---close-the-sandbox)
- [Command Prompt Window Appearance](#command-prompt-window-appearance)
- [Networking Variant (for Contributors)](#networking-variant-for-contributors)
- [Troubleshooting](#troubleshooting)
- [Adding to the Repo](#adding-to-the-repo)

---

## How It Differs from the GUI Sandbox

| | GUI Sandbox | CLI Sandbox |
|---|---|---|
| Runs | Portable `BookmarkRescue.exe` | Python source via `python -m core.*` plus `BookmarkRescue.exe` |
| Networking | Disabled | Disabled (optional networking-enabled variant available) |
| Python required | No | Yes - installed from local file |
| Setup time | ~30 sec | ~90 sec (local Python install) |
| Mock data | `C:\Bookmark_Rescue\Windows.old\` | Same shared folder |
| Repo path | Not needed | `C:\Bookmark-Rescue-Toolkit` (mapped directly) |

---

## File Placement

All files live alongside the GUI sandbox files:

```
C:\Bookmark_Rescue\Sandbox\
    BRT_CLI_Sandbox.wsb               <- CLI sandbox (offline, no networking)
    BRT_CLI_Sandbox_Net.wsb           <- CLI sandbox (networking on, for pip/GUI)
    cli_launcher_inside.bat           <- spawns visible CMD window inside sandbox
    CLI_SANDBOX_README.md             <- this file
    cli_sandbox_startup.bat           <- CLI session script
    generate_mock_data.py             <- mock data generator (existing)
    GUI_Sandbox.wsb                   <- GUI sandbox (existing)
    GUI_SANDBOX_README.md             <- GUI sandbox guide (existing)
    Launch_CLI_Sandbox.bat            <- CLI sandbox launcher
    Launch_GUI_Sandbox.bat            <- GUI sandbox launcher (existing)
    SANDBOX_README.md                 <- main sandbox readme
    sandbox_startup.bat               <- GUI sandbox startup (existing)
    python_installer\
        python-3.12.10-amd64.exe      <- download once, place here
```

---

## Prerequisites

> The CLI sandbox assumes you already have the GUI sandbox set up once (for mock data) and that your repo lives at `C:\Bookmark-Rescue-Toolkit`.

**1. Windows Sandbox enabled**
```
OptionalFeatures.exe -> tick "Windows Sandbox" -> OK -> restart
```

**2. Python installer downloaded**

Download the Python 3.12.10 Windows 64-bit installer once from:

[https://www.python.org/downloads/release/python-31210/](https://www.python.org/downloads/release/python-31210/)

Scroll to "Files" and choose "[Windows installer (64-bit)](https://www.python.org/ftp/python/3.12.10/python-3.12.10.exe)".

Save the file to:
```
C:\Bookmark_Rescue\Sandbox\python_installer\
```

The launcher checks for this file and opens the folder and download page automatically if it is missing.

> **Important:** The download must be done on your **host machine** before launching the sandbox. The sandbox runs with networking disabled by default, so the Python website will not open from inside it. Visit `https://www.python.org/downloads/` on your host, download the installer, and place it in the `python_installer\` folder. The launcher will find it automatically on the next run.
> 
> If you are using the networking-enabled variant (`BRT_CLI_Sandbox_Net.wsb`), the sandbox can reach the internet but Python still needs to be pre-installed from the local file since it is required before pip can run.

**Note**: The CLI sandbox is developed and tested with [Python 3.12.10 64-bit](https://www.python.org/downloads/release/python-31210/). 

**3. Mock data must exist**

The CLI sandbox reuses `C:\Bookmark_Rescue\Windows.old\` from the GUI sandbox. 
If you have not generated it yet, run the GUI sandbox launcher first:
```
C:\Bookmark_Rescue\Sandbox\Launch_GUI_Sandbox.bat
```
You can close the sandbox window once it opens - you only need the launcher to run so it generates the mock data on the host.

**4. Repo must be at the expected path**

The CLI sandbox maps your repo directly into the sandbox at the same path:
```
C:\Bookmark-Rescue-Toolkit\
```
If your repo is elsewhere, update the `HostFolder` path in `BRT_CLI_Sandbox.wsb`.

---

## Usage

### Step 1 - Run the launcher

Double-click:   
```
C:\Bookmark_Rescue\Sandbox\Launch_CLI_Sandbox.bat
```
> **Security warning on first run**: If Windows shows an "Unknown Publisher" warning, right-click `Launch_CLI_Sandbox.bat` > Properties > tick **Unblock** > OK. One-time fix. Does not affect git clones, only zip downloads.

> **Note**: The launcher always opens `BRT_CLI_Sandbox.wsb` (the offline variant). To use the networking variant, double-click `BRT_CLI_Sandbox_Net.wsb` directly after the launcher has confirmed all prerequisites are in place.

The launcher checks all prerequisites and prints their status:

```
[OK] Windows Sandbox available.
[OK] Repo found.
[OK] Mock data found.
[OK] Python installer found.
[OK] Screenshots folder ready.
All checks passed. Launching sandbox...
```

If any check fails, the launcher pauses and explains exactly what is missing.

### Step 2 - Wait for setup (~90 seconds)

The sandbox opens and a maximized Command Prompt window appears automatically. 
You will see numbered steps as each part of setup completes:

```
Step 1/4: Setting dark theme...
[OK] Dark theme applied.

Step 2/4: Installing Python...
Found: C:\...\python-3.12.10-amd64.exe
Installing silently - this takes 60-90 seconds...
Install command finished with exit code: 0
[OK] Python ready.

Step 3/4: Checking repo...
[OK] Repo found at C:\Bookmark-Rescue-Toolkit

Step 4/4: Creating workspace...
[OK] Workspace ready.

Preparing Desktop...
[OK] Desktop ready.
Creating desktop shortcuts...
[OK] Shortcuts created.
 
============================================================
 SETUP COMPLETE - Ready for CLI screenshots
============================================================

Press any key to begin the screenshot session...

```

### Step 3 - Screenshot each command

The session runs through five commands automatically, pausing after each:

```
-----------------------------------------------------------
 SCREENSHOT: Desktop\Screenshots\01-cli-retriever.png
-----------------------------------------------------------
Press any key to continue . . .
```

Open Snipping Tool from the Start menu, capture the Command Prompt window, and save to `Desktop\Screenshots\` using the suggested filename.

> **Note:** `Win+Shift+S` copies to clipboard only inside Windows Sandbox and does not prompt to save. Use Snipping Tool > File > Save As instead.

Files appear immediately in `C:\Bookmark_Rescue\Screenshots\` on your host.

### Step 4 - Commands in sequence

| Step | Command shown | Suggested filename |
|---|---|---|
| 1 | `python -m core.retriever` | `01-cli-retriever.png` |
| 2 | `python -m core.search ... "github"` | `02-cli-search.png` |
| 3 | `python -m core.vault_builder` | `03-cli-vault.png` |
| 4 | `python -m core.bookmark_merger` | `04-cli-merger.png` |
| 5 | `python -m core.retriever --help` | `05-cli-help.png` (optional) |

The prompt shown in each screenshot reads:
```
C:\Bookmark-Rescue-Toolkit>
```
This matches exactly what a user following the documentation would see on their own machine.

### Step 5 - Free exploration (optional)

After the final `Press any key to continue` the session script exits and leaves you at a live Command Prompt in the repo directory:

```
C:\Bookmark-Rescue-Toolkit>
```

Python is fully installed and the workspace folders are all populated from the scripted run. You can run any CLI tool directly from here:

**Re-run the search with a different query**  
```
python -m core.search --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" "youtube"
```

**Export to CSV**  
```
python -m core.bookmark_merger --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" --export-csv "C:\Bookmark_Rescue\3_Merged\bookmarks.csv"
```

**Export to JSON**  
```
python -m core.bookmark_merger --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" --export-json "C:\Bookmark_Rescue\3_Merged\bookmarks.json"
```

**Check any tool's options**  

```
python -m core.search --help
```

```
python -m core.bookmark_merger --help
```

```
python -m core.vault_builder --help
```

**Run the archive beautifier (CLI-only tool)**  
```
python -m core.archive_beautifier "C:\Bookmark_Rescue\1_Raw_Extracted_Data" "C:\Bookmark_Rescue\Archive"
```

This is also useful for capturing any additional screenshots not covered by the scripted session, or for testing changes to the core engines without leaving the sandbox.

**Launching the portable GUI**  

The repo is mapped at `C:\Bookmark-Rescue-Toolkit` which includes the `dist\` folder, so the portable app is already inside the CLI sandbox. You can launch it directly after the CLI session to pick up the GUI flow without leaving the sandbox:

```
C:\Bookmark-Rescue-Toolkit\dist\Bookmark-Rescue-Toolkit\BookmarkRescue.exe
```

The extraction output in `C:\Bookmark_Rescue\1_Raw_Extracted_Data` from the CLI session is ready to use immediately in Tabs 4 and 5 of the GUI.

**Re-running the session**  
To run through the scripted command sequence again without closing the sandbox, call the startup script directly from the prompt:

```
C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\cli_sandbox_startup.bat
```

Python and the workspace are already in place so steps 1-4 complete
almost instantly and the session jumps straight into the command sequence.

### Step 6 - Close the sandbox

Once finished, close the sandbox window. All changes inside are discarded. 
Your screenshots remain in `C:\Bookmark_Rescue\Screenshots\`.

---

## Command Prompt Window Appearance

The startup script applies the following styling:

- Black background, bright white text (`color 0F`)
- 100 columns wide, 45 lines tall
- Title bar: `Bookmark Rescue Toolkit - CLI Demo`
- Each command screen clears before running
- Consistent header on every screen:

```
============================================================
 Bookmark Rescue Toolkit  v1.0.0
============================================================
```

Dark mode is applied to the sandbox via registry before Explorer loads, so folder windows opened during the session also appear in dark mode.

**Command Prompt window dark mode**: The initial CMD window that auto-launches opens in the sandbox default theme. If you prefer a dark terminal for screenshots, open a new Command Prompt from the Start menu after setup completes, new windows pick up the dark registry settings and open with a black background automatically.

---

## Networking Variant (for Contributors)

The default `BRT_CLI_Sandbox.wsb` has networking disabled. This is intentional for screenshot sessions - clean, isolated, no external calls.

A second variant `BRT_CLI_Sandbox_Net.wsb` enables networking. This allows:

- `pip install customtkinter` so `python gui.py` can be tested inside the sandbox
- Any other package installs a contributor might need
- Testing the full GUI alongside the CLI tools in one environment

To create it, make a copy of `BRT_CLI_Sandbox.wsb`, rename it `BRT_CLI_Sandbox_Net.wsb`, and change one line:

```xml
<!-- Change this: -->
<Networking>Disable</Networking>

<!-- To this: -->
<Networking>Enable</Networking>
```

Launch it the same way - use `Launch_CLI_Sandbox.bat` which opens whichever WSB is specified. To switch variants, either edit the launcher's WSB reference or just double-click the WSB file directly.

> **Note on security:** Windows Sandbox is fully isolated from the host by design. Enabling networking inside the sandbox carries no risk to your host machine or files - everything inside the sandbox is discarded on close. The offline default is simply cleaner and more predictable for screenshot sessions.

With networking enabled, once setup completes and the scripted session exits back to the prompt, install customtkinter manually:

```
pip install customtkinter
```

Then launch the GUI:

```
cd C:\Bookmark-Rescue-Toolkit
python gui.py
```

The GUI and all CLI tools are then available in the same sandbox session.

---

## Troubleshooting

**Command Prompt window does not appear after sandbox loads**:  
The LogonCommand fires a small launcher script that waits 6 seconds before opening the Command Prompt window. If nothing appears after 30 seconds, check that `cli_launcher_inside.bat` is present in `C:\Bookmark_Rescue\Sandbox\`.

**Python install fails or times out**:  
Confirm the installer file is a genuine Python 3.12 64-bit Windows installer (`python-3.12.x-amd64.exe`). The 32-bit installer will install but may not be found on the PATH correctly.

**Repo not found error at Step 3**:  
The repo must be at `C:\Bookmark-Rescue-Toolkit\` on the host. If it is elsewhere, update the `HostFolder` in `BRT_CLI_Sandbox.wsb` to match.

**Mock data not found**:  
Run `Launch_GUI_Sandbox.bat` first - it generates `C:\Bookmark_Rescue\Windows.old\` which both sandboxes share.

**Screenshots not appearing on host**:  
Save to `C:\Users\WDAGUtilityAccount\Desktop\Screenshots\` inside the sandbox. That folder is mapped directly to `C:\Bookmark_Rescue\Screenshots\` on the host and files sync instantly.

---

## Adding to the Repo

These files belong in the `sandbox/` folder alongside the GUI sandbox files. They are excluded from the dist build automatically since `sandbox/` is not in `ASSETS_TO_COPY` in `build.py`.

Suggested `sandbox/` structure for the repo:

```
sandbox/                          <- not included in dist build
    BRT_CLI_Sandbox.wsb
    BRT_CLI_Sandbox_Net.wsb       <- one-line network variant, created from BRT_CLI_Sandbox.wsb
    cli_launcher_inside.bat
    CLI_SANDBOX_README.md
    cli_sandbox_startup.bat
    generate_mock_data.py
    GUI_Sandbox.wsb
    GUI_SANDBOX_README.md
    Launch_GUI_Sandbox.bat
    Launch_CLI_Sandbox.bat
    SANDBOX_README.md
    sandbox_startup.bat
```

No `.gitignore` changes are needed. The `python_installer\` subfolder should not be committed - add it locally after cloning.

For details on the GUI sandbox and shared mock data layout, see [SANDBOX_README.md](SANDBOX_README.md) for shared setup and an overview of both environments.
