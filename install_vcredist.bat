@echo off
echo =======================================================
echo    Installing Microsoft Visual C++ 2015-2022 x64
echo    (Required for faster-whisper on Windows VPS)
echo =======================================================
echo.

set VC_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe
set VC_INSTALLER=vc_redist.x64.exe

echo [*] Downloading Visual C++ Redistributable...
powershell -Command "Invoke-WebRequest -Uri '%VC_URL%' -OutFile '%VC_INSTALLER%'"

if exist "%VC_INSTALLER%" (
    echo [*] Installing Visual C++ Runtime (quiet mode)...
    start /wait %VC_INSTALLER% /passive /norestart
    echo [SUCCESS] Visual C++ Redistributable installed successfully!
    del %VC_INSTALLER%
) else (
    echo [ERROR] Failed to download %VC_INSTALLER%.
    echo Please download and run manually from: https://aka.ms/vs/17/release/vc_redist.x64.exe
)

echo.
echo =======================================================
echo You can now run run.bat to use faster-whisper!
echo =======================================================
pause
