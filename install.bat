@echo off
REM ──────────────────────────────────────────────
REM  TrackWasher — Install (Windows CMD)
REM ──────────────────────────────────────────────

echo.
echo   TrackWasher — Installer
echo   ─────────────────────────────────

REM ── Find a native Windows Python (skip MSYS2 / Cygwin) ──
set "PYTHON="
for /f "tokens=*" %%P in ('where python 2^>nul') do (
    echo %%P | findstr /i /c:"msys" /c:"cygwin" >nul
    if errorlevel 1 (
        if not defined PYTHON set "PYTHON=%%P"
    )
)
REM Fallback: accept any python if no native one was found
if not defined PYTHON (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo   [ERROR] Python 3 not found. Install it from https://www.python.org
        pause
        exit /b 1
    )
    for /f "tokens=*" %%P in ('where python') do (
        if not defined PYTHON set "PYTHON=%%P"
    )
)

echo   Using: %PYTHON%
"%PYTHON%" --version

REM ── Create venv ──
if not exist "%~dp0.venv" (
    echo   Creating virtual environment...
    "%PYTHON%" -m venv "%~dp0.venv"
) else (
    echo   Virtual environment already exists.
)

REM ── Find pip in venv ──
if exist "%~dp0.venv\Scripts\pip.exe" (
    set "VPIP=%~dp0.venv\Scripts\pip.exe"
) else if exist "%~dp0.venv\bin\pip.exe" (
    set "VPIP=%~dp0.venv\bin\pip.exe"
) else (
    echo   [ERROR] pip not found in virtual environment.
    pause
    exit /b 1
)

REM ── Install dependencies ──
echo   Installing dependencies...
REM Use python -m pip for the self-upgrade (pip.exe can't overwrite itself)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip -q
) else if exist "%~dp0.venv\bin\python.exe" (
    "%~dp0.venv\bin\python.exe" -m pip install --upgrade pip -q
)
"%VPIP%" install -r "%~dp0requirements.txt" -q

echo.
echo   Done! Run the app with:
echo     start.bat
echo.
pause
