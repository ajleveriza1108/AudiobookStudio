param(
    [switch]$Quick
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host "============================================================"
Write-Host "Audiobook Studio v0.3.0 Verification R1.16"
Write-Host "============================================================"

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    Write-Host "[FAIL] The dedicated project runtime is missing." -ForegroundColor Red
    Write-Host "Run: .\repair_runtime.ps1 -ForceRebuild"
    exit 1
}

Write-Host "Python runtime: $VenvPython"
$env:PYTHONNOUSERSITE = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:CUDA_VISIBLE_DEVICES = ""
$arguments = @("-u", "verify_phase3.py")
if ($Quick) { $arguments += "--quick" }

& $VenvPython @arguments
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ""
    Write-Host "[FAIL] Audiobook Studio verification did not pass (exit code $code)." -ForegroundColor Red
    Write-Host "The runtime is already isolated. Review Logs\native_crash.log for the exact failing thread before any runtime rebuild."
    exit $code
}

Write-Host ""
Write-Host "[PASS] Audiobook Studio verification passed." -ForegroundColor Green
exit 0
