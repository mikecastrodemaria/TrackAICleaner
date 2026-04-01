@echo off
REM ──────────────────────────────────────────────
REM  TrackWasher — Start (Windows CMD)
REM ──────────────────────────────────────────────

if not exist "%~dp0.venv" (
    echo   Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

REM Activate venv (handle both Scripts and bin layouts)
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\bin\activate.bat" (
    call "%~dp0.venv\bin\activate.bat"
)

REM Find streamlit in venv
if exist "%~dp0.venv\Scripts\streamlit.exe" (
    set "STREAMLIT=%~dp0.venv\Scripts\streamlit.exe"
) else if exist "%~dp0.venv\bin\streamlit.exe" (
    set "STREAMLIT=%~dp0.venv\bin\streamlit.exe"
) else (
    echo   [ERROR] streamlit not found. Run install.bat first.
    pause
    exit /b 1
)

echo.
echo   TrackWasher — Starting Streamlit UI...
echo   ─────────────────────────────────────────
echo.

"%STREAMLIT%" run "%~dp0trackwasher.py" --server.headless=false
