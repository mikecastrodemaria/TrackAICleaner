#!/usr/bin/env bash
# ──────────────────────────────────────────────
#  TrackWasher — Start (macOS / Linux)
# ──────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "  Virtual environment not found. Run ./install.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

echo ""
echo "  TrackWasher — Starting Streamlit UI..."
echo "  ─────────────────────────────────────────"
echo ""

streamlit run "$SCRIPT_DIR/trackwasher.py" --server.headless=false
