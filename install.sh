#!/usr/bin/env bash
# ──────────────────────────────────────────────
#  TrackWasher — Install (macOS / Linux)
# ──────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo ""
echo "  TrackWasher — Installer"
echo "  ─────────────────────────────────"

# Check Python
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo "  [ERROR] Python 3 not found. Install it from https://www.python.org"
    exit 1
fi

PY_VERSION=$($PY --version 2>&1)
echo "  Using $PY_VERSION"

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment..."
    $PY -m venv "$VENV_DIR"
else
    echo "  Virtual environment already exists."
fi

# Activate & install
echo "  Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q

echo ""
echo "  Done! Run the app with:"
echo "    ./start.sh"
echo ""
