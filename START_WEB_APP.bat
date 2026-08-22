@echo off
setlocal
title Lastic Productions - Web Downloader
echo ============================================
echo    LASTIC PRODUCTIONS - WEB DOWNLOADER
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on this PC.
    echo         1. Install it free from:  https://www.python.org/downloads/
    echo         2. IMPORTANT: tick "Add Python to PATH" in the installer.
    echo         3. Run this file again.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
)

echo [2/3] Installing dependencies ^(first run only^)...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>nul
pip install flask yt-dlp gunicorn --quiet --disable-pip-version-check

echo [3/3] Starting server...
echo.
echo   * Your browser opens automatically at http://127.0.0.1:5001
echo   * Keep this window OPEN while using the downloader.
echo   * Close this window to stop the server.
echo   * MP3 conversion needs FFmpeg: https://www.gyan.dev/ffmpeg/builds/
echo.
cd "Flask app"
python app.py
pause
