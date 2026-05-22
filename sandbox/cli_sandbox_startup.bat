@echo off
:: cli_sandbox_startup.bat
:: Runs automatically inside sandbox via LogonCommand (cmd.exe /K)
:: All output visible in the CMD window that stays open.

:: ── Dark mode restart trick ─────────────────────────────────────────────
:: On first run: set registry colors, create a flag file, open a fresh
:: CMD window (which now picks up the registry settings), and exit.
:: On second run: flag file exists, delete it and continue normally.
:: A temp file is used as the flag because env vars do not persist
:: across separate CMD processes.
if exist "%TEMP%\brt_dark.flag" (
    del "%TEMP%\brt_dark.flag" >nul 2>&1
    goto :main
)

:: First run - set colors then reopen in a fresh window
reg add "HKCU\Console\BRT CLI Demo" /v ScreenColors /t REG_DWORD /d 0x0F /f >nul 2>&1
reg add "HKCU\Console\BRT CLI Demo" /v ColorTable00 /t REG_DWORD /d 0x00000000 /f >nul 2>&1
reg add "HKCU\Console\BRT CLI Demo" /v ColorTable15 /t REG_DWORD /d 0x00FFFFFF /f >nul 2>&1
reg add "HKCU\Console" /v ScreenColors /t REG_DWORD /d 0x0F /f >nul 2>&1
echo.> "%TEMP%\brt_dark.flag"
start "BRT CLI Demo" /MAX cmd.exe /T:0F /K C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\cli_sandbox_startup.bat
exit

:main
color 0F
cls
mode con: cols=100 lines=45
title Bookmark Rescue Toolkit - CLI Demo

echo.
echo  ============================================================
echo   Bookmark Rescue Toolkit - CLI Screenshot Session
echo  ============================================================
echo.
echo  Step 1/6: Setting dark theme...

:: Dark theme registry - set BEFORE restarting Explorer
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v SystemUsesLightTheme /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Console" /v ScreenColors /t REG_DWORD /d 0x0F /f >nul 2>&1

:: Restart Explorer to apply dark theme
taskkill /f /im explorer.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start "" explorer.exe
timeout /t 3 /nobreak >nul
echo  [OK] Dark theme applied.

echo.
echo  Step 2/6: Installing Python...
echo  Looking for installer in:
echo    C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\python_installer\
echo.

:: Use explicit filename detection - no wildcard
set PY_INSTALLER=
for %%f in ("C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\python_installer\*.exe") do (
    set PY_INSTALLER=%%~f
    echo  Found: %%~f
)

if "%PY_INSTALLER%"=="" (
    echo  [ERROR] No .exe found in python_installer folder.
    echo  Check the folder mapping in BRT_CLI_Sandbox.wsb.
    echo.
    pause
    exit /b 1
)

echo  Installing silently - this takes 60-90 seconds...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Shortcuts=0 Include_launcher=0 Include_test=0
echo  Install command finished with exit code: %ERRORLEVEL%

:: Add Python to PATH for this session
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

echo  Checking Python availability...
python --version
if errorlevel 1 (
    echo  [ERROR] python not found in PATH after install.
    echo  PATH = %PATH%
    pause
    exit /b 1
)
echo  [OK] Python ready.

echo.
echo  Step 3/4: Checking repo...
if not exist "C:\Bookmark-Rescue-Toolkit\gui.py" (
    echo  [ERROR] Repo not found at C:\Bookmark-Rescue-Toolkit
    echo  Check the WSB folder mapping and try again.
    pause
    exit /b 1
)
echo  [OK] Repo found at C:\Bookmark-Rescue-Toolkit

echo.
echo  Step 4/4: Creating workspace...
mkdir "C:\Bookmark_Rescue" >nul 2>&1
mkdir "C:\Bookmark_Rescue\1_Raw_Extracted_Data" >nul 2>&1
mkdir "C:\Bookmark_Rescue\2_Vault_Site" >nul 2>&1
mkdir "C:\Bookmark_Rescue\3_Merged" >nul 2>&1

:: Only copy mock data if C:\Windows.old does not already exist
:: On re-runs this is skipped entirely to avoid xcopy overwrite prompts
if not exist "C:\Windows.old\Users" (
    xcopy /E /I /Q /Y "C:\Users\WDAGUtilityAccount\Desktop\MockSource" "C:\Windows.old\" >nul 2>&1
    if not exist "C:\Windows.old\Users" (
        echo  [ERROR] Mock data copy failed.
        pause
        exit /b 1
    )
    echo  [OK] Workspace ready.
) else (
    echo  [OK] Workspace already exists - skipping mock data copy.
)

echo  Creating desktop shortcuts...
:: Shortcut to Notes folder inside SandboxTools
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Notes.lnk'); $s.TargetPath='%USERPROFILE%\Desktop\SandboxTools\notes'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\1_Raw_Extracted_Data.lnk'); $s.TargetPath='C:\Bookmark_Rescue\1_Raw_Extracted_Data'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\2_Vault_Site.lnk'); $s.TargetPath='C:\Bookmark_Rescue\2_Vault_Site'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\3_Merged.lnk'); $s.TargetPath='C:\Bookmark_Rescue\3_Merged'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Windows.old.lnk'); $s.TargetPath='C:\Windows.old'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Screenshots.lnk'); $s.TargetPath='%USERPROFILE%\Desktop\Screenshots'; $s.Save()" >nul 2>&1
echo  [OK] Shortcuts created.

echo.
echo  ============================================================
echo   SETUP COMPLETE - Ready for CLI screenshots
echo  ============================================================
echo.
echo  Press any key to begin the screenshot session...
pause >nul

cd /d C:\Bookmark-Rescue-Toolkit

:: ── COMMAND 1: Retriever ─────────────────────────────────────────────────
cls
echo  ============================================================
echo   Bookmark Rescue Toolkit  v1.0.0
echo  ============================================================
echo.
echo  C:\Bookmark-Rescue-Toolkit^> python -m core.retriever "C:\Windows.old" "C:\Bookmark_Rescue\1_Raw_Extracted_Data"
echo.
python -m core.retriever "C:\Windows.old" "C:\Bookmark_Rescue\1_Raw_Extracted_Data"
echo.
echo  -----------------------------------------------------------
echo   SCREENSHOT: Desktop\Screenshots\01-cli-retriever.png
echo  -----------------------------------------------------------
pause

:: ── COMMAND 2: Search ────────────────────────────────────────────────────
cls
echo  ============================================================
echo   Bookmark Rescue Toolkit  v1.0.0
echo  ============================================================
echo.
echo  C:\Bookmark-Rescue-Toolkit^> python -m core.search --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" "github"
echo.
python -m core.search --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" "github"
echo.
echo  -----------------------------------------------------------
echo   SCREENSHOT: Desktop\Screenshots\02-cli-search.png
echo  -----------------------------------------------------------
pause

:: ── COMMAND 3: Vault Builder ─────────────────────────────────────────────
cls
echo  ============================================================
echo   Bookmark Rescue Toolkit  v1.0.0
echo  ============================================================
echo.
echo  C:\Bookmark-Rescue-Toolkit^> python -m core.vault_builder "C:\Bookmark_Rescue\1_Raw_Extracted_Data" "C:\Bookmark_Rescue\2_Vault_Site"
echo.
python -m core.vault_builder "C:\Bookmark_Rescue\1_Raw_Extracted_Data" "C:\Bookmark_Rescue\2_Vault_Site"
echo.
echo  -----------------------------------------------------------
echo   SCREENSHOT: Desktop\Screenshots\03-cli-vault.png
echo  -----------------------------------------------------------
pause

:: ── COMMAND 4: Merger ────────────────────────────────────────────────────
cls
echo  ============================================================
echo   Bookmark Rescue Toolkit  v1.0.0
echo  ============================================================
echo.
echo  C:\Bookmark-Rescue-Toolkit^> python -m core.bookmark_merger --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" -o "C:\Bookmark_Rescue\3_Merged\Merged_Bookmarks.html"
echo.
python -m core.bookmark_merger --raw "C:\Bookmark_Rescue\1_Raw_Extracted_Data" -o "C:\Bookmark_Rescue\3_Merged\Merged_Bookmarks.html"
echo.
echo  -----------------------------------------------------------
echo   SCREENSHOT: Desktop\Screenshots\04-cli-merger.png
echo  -----------------------------------------------------------
pause

:: ── COMMAND 5: Help (optional) ───────────────────────────────────────────
cls
echo  ============================================================
echo   Bookmark Rescue Toolkit  v1.0.0
echo  ============================================================
echo.
echo  C:\Bookmark-Rescue-Toolkit^> python -m core.retriever --help
echo.
python -m core.retriever --help
echo.
echo  -----------------------------------------------------------
echo   SCREENSHOT (optional): Desktop\Screenshots\05-cli-help.png
echo   Press any key to end session.
echo  -----------------------------------------------------------
pause

cls
echo.
echo  Session complete. Screenshots saved to Desktop\Screenshots\
echo  (also at C:\Bookmark_Rescue\Screenshots\ on your host)
echo.
