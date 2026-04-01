# ----------------------------------------------
#  TrackWasher - Start (Windows PowerShell)
# ----------------------------------------------

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"

if (-not (Test-Path $VenvDir)) {
    Write-Host "  Virtual environment not found. Run .\install.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate venv (handle both Scripts and bin layouts)
$ActivatePs1 = Join-Path $VenvDir "Scripts\Activate.ps1"
$ActivateAlt  = Join-Path $VenvDir "bin\Activate.ps1"
if (Test-Path $ActivatePs1) {
    & $ActivatePs1
} elseif (Test-Path $ActivateAlt) {
    & $ActivateAlt
}

# Find streamlit in venv
$Streamlit = Join-Path $VenvDir "Scripts\streamlit.exe"
if (-not (Test-Path $Streamlit)) {
    $Streamlit = Join-Path $VenvDir "bin\streamlit.exe"
}
if (-not (Test-Path $Streamlit)) {
    Write-Host "  [ERROR] streamlit not found. Run .\install.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  TrackWasher - Starting Streamlit UI..."
Write-Host "  -----------------------------------------"
Write-Host ""

& $Streamlit run (Join-Path $ScriptDir "trackwasher.py") --server.headless=false
