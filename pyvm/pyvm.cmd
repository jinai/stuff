@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: ------------------------------------------------------------
:: Detect script directory (the folder where pyvm.cmd lives)
:: ------------------------------------------------------------
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"  :: Trim trailing slash

:: ------------------------------------------------------------
:: Locate pyvm.ps1 next to this CMD file
:: ------------------------------------------------------------
set "PYVM_PS1=%SCRIPT_DIR%\pyvm.ps1"

if not exist "%PYVM_PS1%" (
    echo ERROR: Cannot find pyvm.ps1 in "%SCRIPT_DIR%"
    exit /b 1
)

:: ------------------------------------------------------------
:: Pass arguments safely
:: Manual reconstruction breaks quoting, but direct forwarding
:: via %* to PowerShell preserves all arguments correctly.
:: ------------------------------------------------------------
set "PS_ARGS=%*"

:: ------------------------------------------------------------
:: Prefer PowerShell 7+ (pwsh) if available
:: ------------------------------------------------------------
where pwsh >nul 2>nul
if %ERRORLEVEL%==0 (
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PYVM_PS1%" %PS_ARGS%
    exit /b !ERRORLEVEL!
)

:: ------------------------------------------------------------
:: Fallback: Windows PowerShell
:: ------------------------------------------------------------
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PYVM_PS1%" %PS_ARGS%
exit /b !ERRORLEVEL!
