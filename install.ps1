# ──────────────────────────────────────────────
#  TrackWasher — Install (Windows PowerShell)
# ──────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"

Write-Host ""
Write-Host "  TrackWasher - Installer"
Write-Host "  ─────────────────────────────────"

# Check Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "  [ERROR] Python 3 not found. Install it from https://www.python.org" -ForegroundColor Red
    exit 1
}

python --version

# Create venv
if (-not (Test-Path $VenvDir)) {
    Write-Host "  Creating virtual environment..."
    python -m venv $VenvDir
} else {
    Write-Host "  Virtual environment already exists."
}

# Install dependencies
Write-Host "  Installing dependencies..."
& "$VenvDir\Scripts\Activate.ps1"
pip install --upgrade pip -q
pip install -r (Join-Path $ScriptDir "requirements.txt") -q

Write-Host ""
Write-Host "  Done! Run the app with:"
Write-Host "    .\start.ps1"
Write-Host ""
