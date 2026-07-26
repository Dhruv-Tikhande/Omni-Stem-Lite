@echo off
echo ===================================================
echo 🚀 Omni-STEM Lite - Windows Backend Setup 🚀
echo ===================================================

echo.
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python is not installed or not added to PATH!
    pause
    exit /b
)
echo ✅ Python found.

echo.
echo [2/4] Creating Virtual Environment (venv)...
if not exist "venv\" (
    python -m venv venv
    echo ✅ Virtual environment created.
) else (
    echo ⚡ Virtual environment already exists. Skipping creation.
)

echo.
echo [3/4] Activating Environment and Upgrading PIP...
call venv\Scripts\activate
python -m pip install --upgrade pip >nul

echo.
echo [4/4] Downloading and Installing Dependencies...
echo This might take a few minutes depending on your internet speed...

rem --- Core API & Server ---
pip install fastapi uvicorn python-multipart

rem --- Phase 1: Ingestion & Voice Engine ---
pip install PyMuPDF Pillow faster-whisper

rem --- Phase 2: AI Vision Models & Optimization ---
pip install torch torchvision accelerate bitsandbytes transformers qwen-vl-utils

echo.
echo ===================================================
echo ✨ SETUP COMPLETE! ✨
echo All dependencies have been successfully installed.
echo ===================================================
echo.
echo To start working, open your terminal in this folder and run:
echo venv\Scripts\activate
echo.
pause