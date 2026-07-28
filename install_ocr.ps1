[CmdletBinding()]
param(
    [switch]$Repair
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host "============================================================"
Write-Host "Audiobook Studio Offline OCR Check R1.7"
Write-Host "============================================================"

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    Write-Host "The dedicated runtime does not exist. Building it now..." -ForegroundColor Yellow
    & (Join-Path $ProjectRoot "repair_runtime.ps1") -ForceRebuild
    exit $LASTEXITCODE
}

if ($Repair) {
    & (Join-Path $ProjectRoot "repair_runtime.ps1") -ForceRebuild
    exit $LASTEXITCODE
}

$env:PYTHONNOUSERSITE = "1"
& $VenvPython -u "Scripts\runtime_health.py" --component rapidocr --initialize-ocr
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "OCR is not healthy. Rebuilding the isolated runtime..." -ForegroundColor Yellow
    & (Join-Path $ProjectRoot "repair_runtime.ps1") -ForceRebuild
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[PASS] Offline OCR is ready inside the project-local runtime." -ForegroundColor Green
exit 0
