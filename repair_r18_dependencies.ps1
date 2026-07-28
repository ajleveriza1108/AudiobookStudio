[CmdletBinding()]
param(
    [string]$ProjectRoot = $PSScriptRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$NativeHelper = Join-Path $ProjectRoot "Scripts\native_process.ps1"

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "The dedicated runtime is missing. Run .\repair_runtime.ps1 -ForceRebuild"
}
if (-not (Test-Path -LiteralPath $NativeHelper -PathType Leaf)) {
    throw "The native process helper is missing: $NativeHelper"
}
. $NativeHelper

Write-Host "Installing the missing direct runtime dependencies..."
$env:PYTHONNOUSERSITE = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$result = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
    "-m", "pip", "install", "--no-cache-dir",
    "psutil>=6.1,<8", "requests>=2.32,<3"
) -WorkingDirectory $ProjectRoot
if ($result.ExitCode -ne 0) {
    throw "The focused runtime dependency repair failed with exit code $($result.ExitCode)."
}

$health = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
    "-u", "Scripts\runtime_health.py", "--component", "psutil"
) -WorkingDirectory $ProjectRoot
if ($health.ExitCode -ne 0) {
    throw "psutil was installed but its system-metrics health check failed."
}

Write-Host "[PASS] The R1.8 runtime dependency repair is complete." -ForegroundColor Green
