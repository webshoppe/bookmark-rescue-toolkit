@echo off
:: ============================================================================
:: Launch_GUI_Sandbox.bat
:: Place in: C:\Bookmark_Rescue\sandbox\
::
:: Two separate root folders (intentional - matches docs and repo naming):
::   C:\Bookmark-Rescue-Toolkit\   <- repo (hyphen)
::   C:\Bookmark_Rescue\           <- screenshot workspace (underscore)
:: ============================================================================
setlocal

set REPO_DIST=C:\Bookmark-Rescue-Toolkit\dist\Bookmark-Rescue-Toolkit
set EXE=%REPO_DIST%\BookmarkRescue.exe
set WORKSPACE=C:\Bookmark_Rescue
set SANDBOX_DIR=%WORKSPACE%\sandbox
set SHOTS_DIR=%WORKSPACE%\Screenshots
set MOCK_DIR=%WORKSPACE%\Windows.old

echo.
echo  ============================================
echo   Bookmark Rescue Toolkit - Sandbox Launcher
echo  ============================================
echo.

:: Check Windows Sandbox
where /q WindowsSandbox.exe >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Windows Sandbox is not enabled.
    echo  Run OptionalFeatures.exe, tick "Windows Sandbox", restart.
    echo.
    pause & exit /b 1
)
echo  [OK] Windows Sandbox available.

:: Check portable app
if not exist "%EXE%" (
    echo.
    echo  [ERROR] BookmarkRescue.exe not found at:
    echo    %EXE%
    echo.
    echo  Build it first:
    echo    cd C:\Bookmark-Rescue-Toolkit
    echo    .venv\Scripts\activate
    echo    python build.py
    echo.
    pause & exit /b 1
)
echo  [OK] Portable app found.

:: Create Screenshots folder
if not exist "%SHOTS_DIR%\" (
    mkdir "%SHOTS_DIR%"
    echo  [OK] Created Screenshots folder.
) else (
    echo  [OK] Screenshots folder exists.
)

:: Generate mock Windows.old if missing
if not exist "%MOCK_DIR%\Users" (
    echo.
    echo  Generating mock Windows.old data...
    python "%SANDBOX_DIR%\generate_mock_data.py"
    if errorlevel 1 (
        echo  [ERROR] Mock data generation failed. Check Python is in PATH.
        pause & exit /b 1
    )
    echo  [OK] Mock data generated at %MOCK_DIR%
) else (
    echo  [OK] Mock data exists. Delete %MOCK_DIR% to regenerate.
)

echo.
echo  -- Paths to use inside the sandbox -----------------------------
echo.
echo   Tab 1  Windows.old Path:    C:\Windows.old
echo   Tab 1  Output Directory:    C:\Bookmark_Rescue\1_Raw_Extracted_Data
echo   Tab 4  Site Output Folder:  C:\Bookmark_Rescue\2_Vault_Site
echo   Tab 5  Merger Output:       C:\Bookmark_Rescue\3_Merged\Merged_Bookmarks.html
echo   Search Search in:           C:\Bookmark_Rescue\1_Raw_Extracted_Data
echo.
echo   Screenshots: save to Desktop\Screenshots (syncs to host live)
echo   Use Snipping Tool directly - Win+Shift+S does not save in Sandbox.
echo  -----------------------------------------------------------------
echo.
echo  Launching sandbox...
echo.

start "" "%SANDBOX_DIR%\GUI_Sandbox.wsb"
:: Open Screenshots folder on the HOST so it's ready to receive shots
timeout /t 3 /nobreak >nul
start "" explorer.exe "%SHOTS_DIR%"
endlocal
