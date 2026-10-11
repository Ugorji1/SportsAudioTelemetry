@echo off
title Sports Audio Telemetry Monitor
echo Starting Real-Time Audio Monitor...

if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found. Running install.bat first...
    call install.bat
)

call venv\Scripts\activate.bat
python monitor.py
pause
