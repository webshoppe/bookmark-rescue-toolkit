@echo off
:: Wait for desktop to settle
timeout /t 6 /nobreak >nul

:: Set colors for the specific window title before it opens.
:: Windows console host reads HKCU\Console\<title> at window creation time.
reg add "HKCU\Console\BRT CLI Demo" /v ScreenColors /t REG_DWORD /d 0x0F /f >nul 2>&1
reg add "HKCU\Console\BRT CLI Demo" /v ColorTable00 /t REG_DWORD /d 0x00000000 /f >nul 2>&1
reg add "HKCU\Console\BRT CLI Demo" /v ColorTable15 /t REG_DWORD /d 0x00FFFFFF /f >nul 2>&1
reg add "HKCU\Console\BRT CLI Demo" /v WindowSize   /t REG_DWORD /d 0x002D0064 /f >nul 2>&1

:: Also set global console default as fallback
reg add "HKCU\Console" /v ScreenColors /t REG_DWORD /d 0x0F /f >nul 2>&1

:: Open the session window - title must match the registry key above exactly
start "BRT CLI Demo" /MAX cmd.exe /T:0F /K C:\Users\WDAGUtilityAccount\Desktop\SandboxScripts\cli_sandbox_startup.bat
