param(
    [string]$ProjectRoot = $PSScriptRoot,
    [switch]$ForceRebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$VenvRoot = Join-Path $ProjectRoot ".voice-venv"
$PythonExe = Join-Path $VenvRoot "Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "Logs"
$NativeHelper = Join-Path $ProjectRoot "Scripts\native_process.ps1"
if (-not (Test-Path -LiteralPath $NativeHelper)) {
    throw "The native process helper is missing: $NativeHelper"
}
. $NativeHelper

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("voice_engine_install_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

function Write-Log([string]$Message) {
    Write-Host $Message
    $Message | Add-Content -LiteralPath $LogFile -Encoding UTF8
}

function Run-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )
    $Result = Invoke-NativeProcess `
        -FilePath $FilePath `
        -Arguments $Arguments `
        -WorkingDirectory $ProjectRoot `
        -CaptureOutput `
        -ShowCapturedOutput `
        -LogPath ($LogFile + ".last-command.log")
    if ($Result.StdOut) { $Result.StdOut | Add-Content -LiteralPath $LogFile -Encoding UTF8 }
    if ($Result.StdErr) { $Result.StdErr | Add-Content -LiteralPath $LogFile -Encoding UTF8 }
    if ($Result.ExitCode -ne 0) {
        throw "$FailureMessage (exit code $($Result.ExitCode)). See $LogFile"
    }
}

Write-Log "============================================================"
Write-Log "Audiobook Studio Optional Voice Engine Installer"
Write-Log "Chatterbox 0.1.7 | isolated Python 3.11 runtime"
Write-Log "============================================================"
Write-Log "Project: $ProjectRoot"
Write-Log "Runtime: $VenvRoot"
Write-Log ""
Write-Log "This module is optional. Kokoro and OCR are not modified."
Write-Log "Only use recordings you own or have permission to clone."
Write-Log ""

$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if (-not $PyLauncher) {
    throw "Python Launcher (py.exe) is required. Install Python 3.11 x64, then run this script again."
}

Run-Checked -FilePath $PyLauncher.Source -Arguments @("-3.11", "-c", "import sys; print(sys.executable); print(sys.version)") -FailureMessage "Python 3.11 x64 is required"

if ($ForceRebuild -and (Test-Path -LiteralPath $VenvRoot)) {
    Write-Log "Removing the previous optional voice runtime..."
    Remove-Item -LiteralPath $VenvRoot -Recurse -Force
}

if (-not (Test-Path -LiteralPath $PythonExe)) {
    Write-Log "Creating the isolated optional voice runtime..."
    Run-Checked -FilePath $PyLauncher.Source -Arguments @("-3.11", "-m", "venv", $VenvRoot) -FailureMessage "Could not create the optional voice runtime"
}

Write-Log "Updating packaging tools..."
Run-Checked -FilePath $PythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") -FailureMessage "Could not update packaging tools"

Write-Log "Installing Chatterbox TTS 0.1.7..."
Run-Checked -FilePath $PythonExe -Arguments @("-m", "pip", "install", "chatterbox-tts==0.1.7") -FailureMessage "Chatterbox installation failed"

Write-Log "Verifying the optional runtime..."
$VerifyCode = "import torch, torchaudio; from chatterbox.tts_turbo import ChatterboxTurboTTS; from chatterbox.mtl_tts import ChatterboxMultilingualTTS; print('torch:', torch.__version__); print('torchaudio:', torchaudio.__version__); print('chatterbox import: PASS')"
Run-Checked -FilePath $PythonExe -Arguments @("-c", $VerifyCode) -FailureMessage "The optional voice runtime did not pass import verification"

$ReadyMarker = Join-Path $VenvRoot ".audiobookstudio_chatterbox_ready.json"
@{
    schema = 1
    package = "chatterbox-tts"
    version = "0.1.7"
    python = "3.11"
    verified_at = (Get-Date).ToString("s")
} | ConvertTo-Json | Set-Content -LiteralPath $ReadyMarker -Encoding UTF8

Write-Log ""
Write-Log "[PASS] Optional voice-cloning runtime installed."
Write-Log "Models download into the portable Models folder on first use."
Write-Log "Close and reopen Audiobook Studio, then open Tools > Voice Studio."
Write-Log "Log: $LogFile"
