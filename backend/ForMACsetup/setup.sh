#!/bin/bash
echo "==================================================="
echo "🚀 Omni-STEM Lite - Mac/Linux Backend Setup 🚀"
echo "==================================================="

echo ""
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 could not be found!"
    exit 1
fi
echo "✅ Python 3 found."

echo ""
echo "[2/4] Creating Virtual Environment (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created."
else
    echo "⚡ Virtual environment already exists. Skipping creation."
fi

echo ""
echo "[3/4] Activating Environment and Upgrading PIP..."
source venv/bin/activate
pip install --upgrade pip

echo ""
echo "[4/4] Downloading and Installing Dependencies..."
echo "This might take a few minutes..."

# Core API & Server
pip install fastapi uvicorn python-multipart

# Phase 1: Ingestion & Voice Engine
pip install PyMuPDF Pillow faster-whisper

# Phase 2: AI Vision Models (Mac uses standard PyTorch, which auto-detects M1/M2 chips)
pip install torch torchvision accelerate transformers qwen-vl-utils

echo ""
echo "==================================================="
echo "✨ SETUP COMPLETE! ✨"
echo "All dependencies have been successfully installed."
echo "==================================================="
echo ""
echo "To start working, run this command in your terminal:"
echo "source venv/bin/activate"
echo ""