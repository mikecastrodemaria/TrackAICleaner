# ----------------------------------------------
#  TrackWasher - Install (Windows PowerShell)
# ----------------------------------------------

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"

Write-Host ""
Write-Host "  TrackWasher - Installer"
Write-Host "  -----------------------------------"

# --Find a native Windows Python (skip MSYS2 / Cygwin) --
$PythonExe = $null
$allPythons = (Get-Command python -All -ErrorAction SilentlyContinue)
foreach ($p in $allPythons) {
    if ($p.Source -notmatch 'msys|cygwin') {
        $PythonExe = $p.Source
        break
    }
}
# Fallback: accept any python
if (-not $PythonExe) {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Write-Host "  [ERROR] Python 3 not found. Install it from https://www.python.org" -ForegroundColor Red
        exit 1
    }
    $PythonExe = $py.Source
}

Write-Host "  Using: $PythonExe"
& $PythonExe --version

# --Create venv --
if (-not (Test-Path $VenvDir)) {
    Write-Host "  Creating virtual environment..."
    & $PythonExe -m venv $VenvDir
} else {
    Write-Host "  Virtual environment already exists."
}

# --Find pip in venv --
$VPip = Join-Path $VenvDir "Scripts\pip.exe"
if (-not (Test-Path $VPip)) {
    $VPip = Join-Path $VenvDir "bin\pip.exe"
}
if (-not (Test-Path $VPip)) {
    Write-Host "  [ERROR] pip not found in virtual environment." -ForegroundColor Red
    exit 1
}

# --Install dependencies --
Write-Host "  Installing dependencies..."
# Use python -m pip for the self-upgrade (pip.exe can't overwrite itself)
$VPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VPython)) { $VPython = Join-Path $VenvDir "bin\python.exe" }
& $VPython -m pip install --upgrade pip -q
& $VPip install -r (Join-Path $ScriptDir "requirements.txt") -q

Write-Host ""
Write-Host "  Done! Run the app with:"
Write-Host "    .\start.ps1"
Write-Host ""
