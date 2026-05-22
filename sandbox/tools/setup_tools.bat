@echo off
:: ============================================================================
:: setup_tools.bat
:: One-time setup script for the BRT Sandbox Tools folder.
:: Run this manually inside either sandbox on first use.
::
:: What it does:
::   1. Installs 7-Zip from the local installer (silent, per-session)
::   2. Creates desktop shortcuts to all tools
::   3. Creates a shortcut to the Notes folder
::   4. Verifies which portable tools are present
::
:: Run again any time to reinstall 7-Zip (required each fresh sandbox session)
:: or to recreate shortcuts if they were lost.
::
:: Tools folder: C:\Users\WDAGUtilityAccount\Desktop\tools\
:: ============================================================================

color 0F
title BRT Sandbox - Tools Setup


echo.
echo  ============================================================
echo   BRT Sandbox Tools Setup
echo  ============================================================
echo.

set TOOLS=C:\Users\WDAGUtilityAccount\Desktop\SandboxTools
set SHOTS=C:\Users\WDAGUtilityAccount\Desktop\Screenshots

:: ── 1. Install 7-Zip ─────────────────────────────────────────────────────
echo  [1/4] Installing 7-Zip...

set ZIP_EXE=
for %%f in (%TOOLS%\7zip_installer\*.exe) do set ZIP_EXE=%%~f

if "%ZIP_EXE%"=="" (
    echo  [SKIP] No 7-Zip installer found in tools\7zip_installer\
    echo         See 7zip_installer\README.md for the download link.
) else (
    "%ZIP_EXE%" /S >nul 2>&1
    echo  [OK]   7-Zip installed.
)

:: ── 2. Desktop shortcuts for each tool ───────────────────────────────────
echo.
echo  [2/4] Creating tool shortcuts on Desktop...

:: Firefox
if exist "%TOOLS%\Firefox\FirefoxPortable.exe" (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Firefox Portable.lnk'); $s.TargetPath='%TOOLS%\Firefox\FirefoxPortable.exe'; $s.Save()" >nul 2>&1
    echo  [OK]   Firefox Portable
) else (
    echo  [MISS] Firefox Portable - not found in tools\Firefox\
)

:: Notepad++
if exist "%TOOLS%\Notepad++\notepad++.exe" (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Notepad++.lnk'); $s.TargetPath='%TOOLS%\Notepad++\notepad++.exe'; $s.Save()" >nul 2>&1
    echo  [OK]   Notepad++
) else (
    echo  [MISS] Notepad++ - not found in tools\Notepad++\
)

:: SumatraPDF
if exist "%TOOLS%\SumatraPDF\SumatraPDF.exe" (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\SumatraPDF.lnk'); $s.TargetPath='%TOOLS%\SumatraPDF\SumatraPDF.exe'; $s.Save()" >nul 2>&1
    echo  [OK]   SumatraPDF
) else (
    echo  [MISS] SumatraPDF - not found in tools\SumatraPDF\
)

:: ShareX
if exist "%TOOLS%\ShareX\ShareX.exe" (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\ShareX.lnk'); $s.TargetPath='%TOOLS%\ShareX\ShareX.exe'; $s.Save()" >nul 2>&1
    echo  [OK]   ShareX
) else (
    echo  [MISS] ShareX - not found in tools\ShareX\
)

:: PeaZip
if exist "%TOOLS%\PeaZip\peazip.exe" (
    powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\PeaZip.lnk'); $s.TargetPath='%TOOLS%\PeaZip\peazip.exe'; $s.Save()" >nul 2>&1
    echo  [OK]   PeaZip
) else (
    echo  [MISS] PeaZip - not found in tools\PeaZip\
)

:: Notes folder shortcut on Desktop
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Notes.lnk'); $s.TargetPath='%TOOLS%\Notes'; $s.Save()" >nul 2>&1
echo  [OK]   Notes folder shortcut

:: ── 3. Configure ShareX save path ────────────────────────────────────────
echo.
echo  [3/4] Configuring ShareX screenshot path...

if exist "%TOOLS%\ShareX\ShareX.exe" (
    echo  [OK]   ShareX found. Screenshots save to Desktop\Screenshots\YYYY\MM
    echo         Config: %TOOLS%\ShareX\ApplicationConfig.json
) else (
    echo  [SKIP] ShareX not found in SandboxTools\ShareX\
)

:: ── 4. Summary ───────────────────────────────────────────────────────────
echo.
echo  [4/4] Summary
echo.
echo  MISS entries above mean the portable was not found in the Tools folder.
echo  Download and place the portable in the correct subfolder, then re-run
echo  this script to create the shortcut.
echo.
echo  See tools\TOOLS_README.md or the individual guides in tools\guides\
echo  for download links and placement instructions for each tool.
echo.
echo  ============================================================
echo   Setup complete. Shortcuts are on the Desktop.
echo  ============================================================
echo.
pause
