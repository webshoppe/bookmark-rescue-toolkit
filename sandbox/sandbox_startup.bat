@echo off
:: sandbox_startup.bat - runs automatically inside the sandbox on login
:: Sets up C:\Bookmark_Rescue\ workspace, copies mock data to C:\Windows.old,
:: creates desktop shortcuts, sets dark theme, launches the app.

timeout /t 4 /nobreak >nul

:: Create workspace matching docs recommended structure
mkdir "C:\Bookmark_Rescue" >nul 2>&1
mkdir "C:\Bookmark_Rescue\1_Raw_Extracted_Data" >nul 2>&1
mkdir "C:\Bookmark_Rescue\2_Vault_Site" >nul 2>&1
mkdir "C:\Bookmark_Rescue\3_Merged" >nul 2>&1

:: Copy mock data to C:\Windows.old (matches what the docs and fields show)
if exist "C:\Users\WDAGUtilityAccount\Desktop\MockSource\Users" (
    xcopy /E /I /Q "C:\Users\WDAGUtilityAccount\Desktop\MockSource" "C:\Windows.old" >nul 2>&1
) else (
    echo [WARN] Mock source not found. Run Launch_BRT_Sandbox.bat on the host first.
)

:: Desktop shortcuts to workspace folders
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\1_Raw_Extracted_Data.lnk'); $s.TargetPath='C:\Bookmark_Rescue\1_Raw_Extracted_Data'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\2_Vault_Site.lnk'); $s.TargetPath='C:\Bookmark_Rescue\2_Vault_Site'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\3_Merged.lnk'); $s.TargetPath='C:\Bookmark_Rescue\3_Merged'; $s.Save()" >nul 2>&1
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%USERPROFILE%\Desktop\Windows.old.lnk'); $s.TargetPath='C:\Windows.old'; $s.Save()" >nul 2>&1

:: Set sandbox to dark theme
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 00000000 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v SystemUsesLightTheme /t REG_DWORD /d 00000000 /f >nul 2>&1

:: Ensure dark mode takes effect before app launches
timeout /t 2 /nobreak >nul

:: Launch BookmarkRescue
start "" "C:\Users\WDAGUtilityAccount\Desktop\BookmarkRescue\BookmarkRescue.exe"

:: Open Screenshots folder
timeout /t 3 /nobreak >nul
start "" explorer.exe "C:\Users\WDAGUtilityAccount\Desktop\Screenshots"

:: Open Sandbox Scripts folder
start "" explorer.exe "C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts"

:: Open BookmarkRescue folder
start "" explorer.exe "C:\Users\WDAGUtilityAccount\Desktop\BookmarkRescue"

:: Open generated mock user data folder
start "" explorer.exe "C:\Windows.old"

:: Open Bookmark Rescue vault parent folder
start "" explorer.exe "C:\Bookmark_Rescue"

:: Open Bookmark Rescue Tab 1 raw data folder
start "" explorer.exe "C:\Bookmark_Rescue\1_Raw_Extracted_Data"

:: Open Bookmark Rescue Tab 4 vault site folder
start "" explorer.exe "C:\Bookmark_Rescue\2_Vault_Site"

:: Open Bookmark Rescue Tab 5 merged bookmarks folder
start "" explorer.exe "C:\Bookmark_Rescue\3_Merged"

:: Open Documents folder
start "" explorer.exe "C:\Bookmark_Rescue"
