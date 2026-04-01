@echo off
REM ──────────────────────────────────────────────
REM  TrackWasher — Install (Windows CMD)
REM ──────────────────────────────────────────────

echo.
echo   TrackWasher — Installer
echo   ─────────────────────────────────

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERROR] Python 3 not found. Install it from https://www.python.org
    pause
    exit /b 1
)

python --version

REM Create venv
if not exist "%~dp0.venv" (
    echo   Creating virtual environment...
    python -m venv "%~dp0.venv"
) else (
    echo   Virtual environment already exists.
)

REM Install dependencies
echo   Installing dependencies...
call "%~dp0.venv\Scripts\activate.bat"
pip install --upgrade pip -q
pip install -r "%~dp0requirements.txt" -q

echo.
echo   Done! Run the app with:
echo     start.bat
echo.
pause
