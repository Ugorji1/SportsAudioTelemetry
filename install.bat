@echo off
echo =======================================================
echo    Sports Audio Telemetry - Windows VPS Installer
echo =======================================================

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ from python.org and make sure to check "Add Python to PATH".
    pause
    exit /b 1
)

:: Create Virtual Environment
if not exist "venv" (
    echo [*] Creating Python virtual environment...
    python -m venv venv
)

:: Activate Virtual Environment & Install Requirements
echo [*] Installing required Python libraries...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

:: Download Speech Model
echo [*] Downloading and setting up Vosk STT speech model...
python setup_model.py

:: Download FFmpeg if not in PATH and not local
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "ffmpeg.exe" (
        echo [*] FFmpeg not found. Downloading standalone ffmpeg.exe...
        python download_ffmpeg.py
    )
)

echo.
echo =======================================================
echo [SUCCESS] Installation complete!
echo 1. Edit config.json with your stream URL and Telegram token.
echo 2. Double-click run.bat to start monitoring.
echo =======================================================
pause
