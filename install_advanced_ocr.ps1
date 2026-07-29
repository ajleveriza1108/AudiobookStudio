param(
    [string]$ProjectRoot = $PSScriptRoot,
    [switch]$ForceRebuild,
    [switch]$AllowExperimental,
    [switch]$SkipModelDownload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$RuntimeRoot = Join-Path $ProjectRoot ".advanced-ocr-venv"
$PythonExe = Join-Path $RuntimeRoot "Scripts\python.exe"
$MainPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$CapabilityScript = Join-Path $ProjectRoot "Scripts\advanced_ocr_capability.py"
$Downloader = Join-Path $ProjectRoot "Scripts\download_unlimited_ocr.py"
$ModelRoot = Join-Path $ProjectRoot "Models\Unlimited-OCR"
$LogDir = Join-Path $ProjectRoot "Logs"
$NativeHelper = Join-Path $ProjectRoot "Scripts\native_process.ps1"
$ReadyMarker = Join-Path $RuntimeRoot ".audiobookstudio_unlimited_ocr_ready.json"

if (-not (Test-Path -LiteralPath $NativeHelper -PathType Leaf)) {
    throw "The native process helper is missing: $NativeHelper"
}
. $NativeHelper
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("advanced_ocr_install_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

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
Write-Log "Audiobook Studio Optional Advanced OCR Installer"
Write-Log "Unlimited-OCR | isolated Python 3.12 CUDA runtime"
Write-Log "============================================================"
Write-Log "Project: $ProjectRoot"
Write-Log "Runtime: $RuntimeRoot"
Write-Log "Model:   $ModelRoot"
Write-Log ""
Write-Log "This optional module does not modify Kokoro, RapidOCR, or the main .venv."
Write-Log "The model download is approximately 6.7 GB; allow at least 20-30 GB free space."
Write-Log ""

if (-not (Test-Path -LiteralPath $MainPython -PathType Leaf)) {
    throw "The verified Audiobook Studio runtime is missing: $MainPython"
}
if (-not (Test-Path -LiteralPath $CapabilityScript -PathType Leaf)) {
    throw "The Advanced OCR capability checker is missing: $CapabilityScript"
}

Write-Log "[1/7] Checking this laptop and recording the result..."
$Capability = Invoke-NativeProcess `
    -FilePath $MainPython `
    -Arguments @("-u", $CapabilityScript) `
    -WorkingDirectory $ProjectRoot `
    -CaptureOutput `
    -ShowCapturedOutput `
    -LogPath ($LogFile + ".capability.log")
if ($Capability.ExitCode -eq 4) {
    throw "This laptop does not meet the minimum Advanced OCR requirements. Use RapidOCR instead."
}
if ($Capability.ExitCode -eq 3 -and -not $AllowExperimental) {
    throw "This laptop is experimental, not supported. Re-run with -AllowExperimental only after reviewing Logs\advanced_ocr_capability.json."
}
if ($Capability.ExitCode -notin @(0, 3)) {
    throw "The Advanced OCR capability check failed with exit code $($Capability.ExitCode)."
}
Write-Log "[PASS] Laptop capability was recorded."

$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if (-not $PyLauncher) {
    throw "Python Launcher (py.exe) is required. Install Python 3.12 x64, then run this script again."
}

Write-Log "[2/7] Verifying Python 3.12 x64..."
Run-Checked -FilePath $PyLauncher.Source -Arguments @("-3.12", "-c", "import struct,sys; assert struct.calcsize('P')*8==64; print(sys.executable); print(sys.version)") -FailureMessage "Python 3.12 x64 is required"

if ($ForceRebuild -and (Test-Path -LiteralPath $RuntimeRoot)) {
    Write-Log "Removing the previous optional Advanced OCR runtime..."
    Remove-Item -LiteralPath $RuntimeRoot -Recurse -Force
}
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    Write-Log "[3/7] Creating the isolated Advanced OCR runtime..."
    Run-Checked -FilePath $PyLauncher.Source -Arguments @("-3.12", "-m", "venv", $RuntimeRoot) -FailureMessage "Could not create the Advanced OCR runtime"
} else {
    Write-Log "[3/7] Existing isolated runtime found."
}

Write-Log "[4/7] Updating packaging tools..."
Run-Checked -FilePath $PythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel") -FailureMessage "Could not update packaging tools"

Write-Log "[5/7] Installing the CUDA PyTorch runtime and official Unlimited-OCR dependencies..."
Run-Checked -FilePath $PythonExe -Arguments @("-m", "pip", "install", "--index-url", "https://download.pytorch.org/whl/cu129", "torch==2.10.0", "torchvision==0.25.0") -FailureMessage "CUDA PyTorch installation failed"
Run-Checked -FilePath $PythonExe -Arguments @(
    "-m", "pip", "install",
    "transformers==4.57.1",
    "Pillow==12.1.1",
    "matplotlib==3.10.8",
    "einops==0.8.2",
    "addict==2.4.0",
    "easydict==1.13",
    "pymupdf==1.27.2.2",
    "psutil==7.2.2",
    "huggingface_hub>=0.34,<1",
    "safetensors>=0.5,<1",
    "accelerate>=1.9,<2"
) -FailureMessage "Unlimited-OCR dependency installation failed"

Write-Log "[6/7] Verifying CUDA, VRAM, and BF16 support..."
$VerifyCode = @"
import json, torch
assert torch.cuda.is_available(), 'CUDA is unavailable in the isolated runtime'
assert torch.cuda.is_bf16_supported(), 'The GPU does not support BF16 safely'
p = torch.cuda.get_device_properties(0)
info = {'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': p.name, 'vram_gb': round(p.total_memory/1024**3, 2)}
assert info['vram_gb'] >= 7.5, 'Less than 8 GB VRAM is not supported'
print(json.dumps(info, indent=2))
"@
Run-Checked -FilePath $PythonExe -Arguments @("-c", $VerifyCode) -FailureMessage "Advanced OCR CUDA verification failed"

if (-not $SkipModelDownload) {
    Write-Log "[7/7] Downloading and verifying the pinned Unlimited-OCR model..."
    Run-Checked -FilePath $PythonExe -Arguments @("-u", $Downloader, $ModelRoot) -FailureMessage "Unlimited-OCR model download or SHA-256 verification failed"
} else {
    Write-Log "[7/7] Model download skipped. The module will remain unavailable until the verified model is installed."
}

if ($SkipModelDownload) {
    Write-Log ""
    Write-Log "[PARTIAL] Runtime installed, but no ready marker was created because the model was skipped."
    Write-Log "Re-run without -SkipModelDownload to finish installation."
    Write-Log "Log: $LogFile"
    exit 0
}

$ModelMarker = Join-Path $ModelRoot ".audiobookstudio_model_verified.json"
if (-not (Test-Path -LiteralPath $ModelMarker -PathType Leaf)) {
    throw "The verified model marker is missing: $ModelMarker"
}
@{
    schema = 1
    engine = "Unlimited-OCR"
    python = "3.12"
    torch = "2.10.0"
    torchvision = "0.25.0"
    transformers = "4.57.1"
    model_id = "baidu/Unlimited-OCR"
    model_revision = "d549bb9d6a055dbe291408916d66acc2cd5920f6"
    verified_at = (Get-Date).ToString("s")
} | ConvertTo-Json | Set-Content -LiteralPath $ReadyMarker -Encoding UTF8

Write-Log ""
Write-Log "[PASS] Optional Advanced OCR runtime and model installed."
Write-Log "Close and reopen Audiobook Studio. Open Settings > OCR and enable the toggle."
Write-Log "RapidOCR remains installed and is used automatically if Advanced OCR rejects a page."
Write-Log "Log: $LogFile"
