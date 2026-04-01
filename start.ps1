# ──────────────────────────────────────────────
#  TrackWasher — Start (Windows PowerShell)
# ──────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"

if (-not (Test-Path $VenvDir)) {
    Write-Host "  Virtual environment not found. Run .\install.ps1 first." -ForegroundColor Red
    exit 1
}

& "$VenvDir\Scripts\Activate.ps1"

Write-Host ""
Write-Host "  TrackWasher - Starting Streamlit UI..."
Write-Host "  ─────────────────────────────────────────"
Write-Host ""

streamlit run (Join-Path $ScriptDir "trackwasher.py") --server.headless=false
