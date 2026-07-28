[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$NativeHelper = Join-Path $ProjectRoot "Scripts\native_process.ps1"
$LogRoot = Join-Path $ProjectRoot "Logs"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$LogPath = Join-Path $LogRoot ("gui_runtime_repair_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
$TargetVersion = "6.8.3"

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "The dedicated runtime is missing. Run .\repair_runtime.ps1 -ForceRebuild"
}
if (-not (Test-Path -LiteralPath $NativeHelper -PathType Leaf)) {
    throw "The native process helper is missing: $NativeHelper"
}
. $NativeHelper

$env:PYTHONNOUSERSITE = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:QT_STYLE_OVERRIDE = "Fusion"
$env:QT_OPENGL = "software"
$env:QT_QUICK_BACKEND = "software"
$env:QSG_RHI_BACKEND = "software"
$env:QT_WIDGETS_RHI = "0"

$versionProbe = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
    "-c", "import PySide6; print(PySide6.__version__)"
) -WorkingDirectory $ProjectRoot -CaptureOutput
$PreviousVersion = ""
if ($versionProbe.ExitCode -eq 0) {
    $PreviousVersion = ([string]$versionProbe.StdOut).Trim()
}

function Restore-PreviousQtRuntime {
    if (-not $PreviousVersion -or $PreviousVersion -eq $TargetVersion) { return }
    Write-Host "Restoring the previous PySide6 $PreviousVersion runtime..." -ForegroundColor Yellow
    $restore = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
        "-m", "pip", "install", "--only-binary=:all:", "--no-cache-dir", "--force-reinstall",
        "PySide6==$PreviousVersion"
    ) -WorkingDirectory $ProjectRoot -CaptureOutput -ShowCapturedOutput
    if ($restore.ExitCode -ne 0) {
        Write-Host "[WARNING] The previous PySide6 runtime could not be restored automatically." -ForegroundColor Yellow
    }
}

Write-Host "============================================================"
Write-Host "Audiobook Studio GUI Runtime Repair R1.12"
Write-Host "============================================================"
Write-Host "Runtime: $VenvPython"
Write-Host "Log: $LogPath"
$CurrentVersionLabel = if ($PreviousVersion) { $PreviousVersion } else { "not importable" }
Write-Host "Current PySide6: $CurrentVersionLabel"
Write-Host "Installing the published Python 3.12 PySide6 $TargetVersion wheel set..."

try {
    $install = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
        "-m", "pip", "install", "--only-binary=:all:", "--no-cache-dir", "--force-reinstall",
        "PySide6==$TargetVersion"
    ) -WorkingDirectory $ProjectRoot -CaptureOutput -ShowCapturedOutput
    @($install.StdOut, $install.StdErr) | Where-Object { $_ } | Set-Content -LiteralPath $LogPath -Encoding UTF8
    if ($install.ExitCode -ne 0) {
        throw "The PySide6 $TargetVersion installation failed with exit code $($install.ExitCode)."
    }

    $health = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
        "-u", "Scripts\runtime_health.py", "--component", "pyside6"
    ) -WorkingDirectory $ProjectRoot -CaptureOutput -ShowCapturedOutput
    if ($health.ExitCode -ne 0) {
        throw "The repaired PySide6 runtime did not pass its version/native health check."
    }

    Write-Host "Running the real Windows backing-store startup probe..."
    $probe = Invoke-NativeProcess -FilePath $VenvPython -Arguments @(
        "-u", "Scripts\gui_startup_probe.py", "--visible-ms", "8000"
    ) -WorkingDirectory $ProjectRoot -CaptureOutput -ShowCapturedOutput
    if ($probe.ExitCode -ne 0) {
        throw "The real Windows GUI probe failed with exit code $($probe.ExitCode). See Logs\startup_stage.json and Logs\native_crash.log."
    }
}
catch {
    $message = $_.Exception.Message
    Restore-PreviousQtRuntime
    throw $message
}

Write-Host ""
Write-Host "[PASS] PySide6 $TargetVersion is installed and the real Windows renderer completed its probe." -ForegroundColor Green
