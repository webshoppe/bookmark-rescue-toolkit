@echo off
:: ============================================================================
:: Launch_CLI_Sandbox.bat
:: ============================================================================
setlocal

set REPO_ROOT=C:\Bookmark-Rescue-Toolkit
set WORKSPACE=C:\Bookmark_Rescue
set SANDBOX_DIR=%WORKSPACE%\Sandbox
set SHOTS_DIR=%WORKSPACE%\Screenshots
set MOCK_DIR=%WORKSPACE%\Windows.old
set PY_DIR=%SANDBOX_DIR%\python_installer

echo.
echo  ================================================
echo   Bookmark Rescue Toolkit - CLI Sandbox Launcher
echo  ================================================
echo.
echo  REPO_ROOT  = %REPO_ROOT%
echo  SANDBOX_DIR= %SANDBOX_DIR%
echo  PY_DIR     = %PY_DIR%
echo  MOCK_DIR   = %MOCK_DIR%
echo.

:: Check Windows Sandbox
echo Checking Windows Sandbox...
where WindowsSandbox.exe >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Windows Sandbox not found.
    echo  Run OptionalFeatures.exe, tick Windows Sandbox, restart.
    echo.
    pause
    exit /b 1
)
echo  [OK] Windows Sandbox available.

:: Check repo source
echo Checking repo source...
if not exist "%REPO_ROOT%\gui.py" (
    echo  [ERROR] gui.py not found at: %REPO_ROOT%
    echo.
    pause
    exit /b 1
)
echo  [OK] Repo found.

:: Check mock data
echo Checking mock data...
if not exist "%MOCK_DIR%\Users" (
    echo  [ERROR] Mock data not found at: %MOCK_DIR%\Users
    echo  Run Launch_BRT_Sandbox.bat first to generate it.
    echo.
    pause
    exit /b 1
)
echo  [OK] Mock data found.

:: Create python_installer folder if missing
if not exist "%PY_DIR%\" mkdir "%PY_DIR%"

:: Find Python installer - wildcard without quotes
echo Searching for Python installer in: %PY_DIR%
echo.
dir "%PY_DIR%\*.exe" 2>nul
echo.

set PY_EXE=
for %%f in (%PY_DIR%\*.exe) do set PY_EXE=%%~f

echo PY_EXE found = [%PY_EXE%]
echo.

if "%PY_EXE%"=="" (
    echo  [ERROR] No .exe found in: %PY_DIR%
    echo.
    echo  Place the Python 3.12 64-bit installer there:
    echo    python-3.12.10-amd64.exe
    echo.
    echo  Download from: https://www.python.org/downloads/
    echo.
    start "" explorer.exe "%PY_DIR%"
    pause
    exit /b 1
)
echo  [OK] Python installer: %PY_EXE%

:: Create Screenshots folder
if not exist "%SHOTS_DIR%\" mkdir "%SHOTS_DIR%"
echo  [OK] Screenshots folder ready.

echo.
echo  All checks passed. Launching sandbox...
echo.
pause

start "" "%SANDBOX_DIR%\BRT_CLI_Sandbox.wsb"
timeout /t 4 /nobreak >nul
start "" explorer.exe "%SHOTS_DIR%"
endlocal