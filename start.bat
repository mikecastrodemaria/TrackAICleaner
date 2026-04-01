@echo off
REM ──────────────────────────────────────────────
REM  TrackWasher — Start (Windows CMD)
REM ──────────────────────────────────────────────

if not exist "%~dp0.venv" (
    echo   Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

call "%~dp0.venv\Scripts\activate.bat"

echo.
echo   TrackWasher — Starting Streamlit UI...
echo   ─────────────────────────────────────────
echo.

streamlit run "%~dp0trackwasher.py" --server.headless=false
