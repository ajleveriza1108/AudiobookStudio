[CmdletBinding()]
param(
    [switch]$ForceRebuild,
    [switch]$SkipVCRuntime,
    [switch]$KeepBrokenEnvironment
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$nativeHelper = Join-Path $ProjectRoot "Scripts\native_process.ps1"
if (-not (Test-Path -LiteralPath $nativeHelper -PathType Leaf)) {
    throw "The native process helper is missing: $nativeHelper"
}
. $nativeHelper

$LogRoot = Join-Path $ProjectRoot "Logs"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogRoot "runtime_repair_$stamp.log"
$VenvRoot = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$TorchVersion = "2.6.0"
$TorchIndex = "https://download.pytorch.org/whl/cpu"
$VCRedistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$VCRedistPath = Join-Path $ProjectRoot "Temp\vc_redist.x64.exe"

function Write-RepairLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Resolve-SystemPython {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $launcher = (Get-Command py).Source
        $probe = Invoke-NativeProcess -FilePath $launcher -Arguments @("-3.12", "-c", "import struct,sys; print(sys.executable); print(struct.calcsize('P')*8)") -WorkingDirectory $ProjectRoot -CaptureOutput
        if ($probe.ExitCode -eq 0) {
            $lines = @($probe.StdOut -split "`r?`n" | Where-Object { $_.Trim() })
            if ($lines.Count -ge 2 -and $lines[-1].Trim() -eq "64") {
                return [pscustomobject]@{ Exe = $launcher; Args = @("-3.12") }
            }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $python = (Get-Command python).Source
        $probe = Invoke-NativeProcess -FilePath $python -Arguments @("-c", "import struct,sys; assert sys.version_info[:2] == (3,12); print(struct.calcsize('P')*8)") -WorkingDirectory $ProjectRoot -CaptureOutput
        if ($probe.ExitCode -eq 0 -and $probe.StdOut.Trim() -eq "64") {
            return [pscustomobject]@{ Exe = $python; Args = @() }
        }
    }
    throw "A 64-bit Python 3.12 installation was not found. Install 64-bit Python 3.12, then run this repair again."
}

function Invoke-Python {
    param(
        [string]$PythonExe,
        [string[]]$Arguments,
        [switch]$CaptureOutput,
        [switch]$ShowCapturedOutput
    )
    $previousNoUserSite = $env:PYTHONNOUSERSITE
    $previousPipCheck = $env:PIP_DISABLE_PIP_VERSION_CHECK
    $env:PYTHONNOUSERSITE = "1"
    $env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
    try {
        return Invoke-NativeProcess -FilePath $PythonExe -Arguments $Arguments -WorkingDirectory $ProjectRoot -CaptureOutput:$CaptureOutput -ShowCapturedOutput:$ShowCapturedOutput
    }
    finally {
        $env:PYTHONNOUSERSITE = $previousNoUserSite
        $env:PIP_DISABLE_PIP_VERSION_CHECK = $previousPipCheck
    }
}

function Test-Component {
    param(
        [string]$PythonExe,
        [string]$Component,
        [switch]$InitializeOCR
    )
    $arguments = @("-u", "Scripts\runtime_health.py", "--component", $Component)
    if ($InitializeOCR) { $arguments += "--initialize-ocr" }
    $result = Invoke-Python -PythonExe $PythonExe -Arguments $arguments -CaptureOutput
    Write-RepairLog "$Component exit code: $($result.ExitCode)"
    if (-not [string]::IsNullOrWhiteSpace($result.StdOut)) { Write-RepairLog $result.StdOut.TrimEnd() }
    if (-not [string]::IsNullOrWhiteSpace($result.StdErr)) { Write-RepairLog $result.StdErr.TrimEnd() }
    return ($result.ExitCode -eq 0)
}

function Install-VCRuntime {
    if ($SkipVCRuntime) {
        Write-Host "Visual C++ runtime repair was skipped." -ForegroundColor Yellow
        Write-RepairLog "Visual C++ runtime repair skipped by parameter."
        return
    }

    Write-Host "Repairing the Microsoft Visual C++ 2015-2022 x64 runtime..."
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $VCRedistPath) | Out-Null
    try {
        Invoke-WebRequest -Uri $VCRedistUrl -OutFile $VCRedistPath -UseBasicParsing
    }
    catch {
        throw "Could not download the official Microsoft Visual C++ runtime installer. $($_.Exception.Message)"
    }

    $arguments = @("/install", "/quiet", "/norestart")
    try {
        $process = Start-Process -FilePath $VCRedistPath -ArgumentList $arguments -Verb RunAs -Wait -PassThru
    }
    catch {
        throw "The Microsoft Visual C++ runtime installation was cancelled or failed to start. $($_.Exception.Message)"
    }

    Write-RepairLog "VC++ redistributable exit code: $($process.ExitCode)"
    if ($process.ExitCode -notin @(0, 1638, 3010)) {
        throw "Microsoft Visual C++ runtime installation failed with exit code $($process.ExitCode)."
    }
    if ($process.ExitCode -eq 3010) {
        Write-Host "The Visual C++ runtime requested a Windows restart. The repair will continue, but restart Windows if native imports still fail." -ForegroundColor Yellow
    }
}

function Move-BrokenVenv {
    if (-not (Test-Path -LiteralPath $VenvRoot -PathType Container)) { return }
    if ($KeepBrokenEnvironment) {
        $destination = Join-Path $ProjectRoot ("_broken_venv_" + $stamp)
        Move-Item -LiteralPath $VenvRoot -Destination $destination -Force
        Write-Host "Previous runtime saved as: $destination"
        Write-RepairLog "Previous venv moved to $destination"
    }
    else {
        Remove-Item -LiteralPath $VenvRoot -Recurse -Force
        Write-RepairLog "Previous venv removed."
    }
}

Write-Host "============================================================"
Write-Host "Audiobook Studio Dedicated Runtime Repair R1.10"
Write-Host "============================================================"
Write-Host "Project: $ProjectRoot"
Write-Host "Log: $LogPath"
Write-RepairLog "Runtime repair started."

if ($env:OS -ne "Windows_NT") {
    throw "This runtime repair is designed for 64-bit Windows."
}

$systemRuntime = Resolve-SystemPython
$systemPython = [string]$systemRuntime.Exe
$systemArgs = @($systemRuntime.Args)
Write-Host "System Python: $systemPython $($systemArgs -join ' ')"

$existingHealthy = $false
if ((Test-Path -LiteralPath $VenvPython -PathType Leaf) -and -not $ForceRebuild) {
    Write-Host "Checking the existing project runtime..."
    $torchHealthy = Test-Component -PythonExe $VenvPython -Component "torch"
    $onnxHealthy = Test-Component -PythonExe $VenvPython -Component "onnxruntime"
    $ocrHealthy = Test-Component -PythonExe $VenvPython -Component "rapidocr" -InitializeOCR
    $kokoroHealthy = Test-Component -PythonExe $VenvPython -Component "kokoro"
    $pysideHealthy = Test-Component -PythonExe $VenvPython -Component "pyside6"
    $psutilHealthy = Test-Component -PythonExe $VenvPython -Component "psutil"
    $existingHealthy = $torchHealthy -and $onnxHealthy -and $ocrHealthy -and $kokoroHealthy -and $pysideHealthy -and $psutilHealthy
    if ($existingHealthy) {
        Write-Host "[PASS] The project-local runtime is already healthy." -ForegroundColor Green
        exit 0
    }
}

Install-VCRuntime
Move-BrokenVenv

Write-Host "Creating a clean project-local .venv..."
$venvResult = Invoke-NativeProcess -FilePath $systemPython -Arguments (@($systemArgs) + @("-m", "venv", ".venv")) -WorkingDirectory $ProjectRoot
if ($venvResult.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    throw "The project-local virtual environment could not be created."
}

Write-Host "Updating pip, setuptools, and wheel..."
$tools = Invoke-Python -PythonExe $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
if ($tools.ExitCode -ne 0) { throw "Python packaging tools could not be installed." }

Write-Host "Installing PyTorch $TorchVersion CPU from the official PyTorch wheel index..."
$torchInstall = Invoke-Python -PythonExe $VenvPython -Arguments @(
    "-m", "pip", "install", "--no-cache-dir", "--force-reinstall",
    "torch==$TorchVersion", "--index-url", $TorchIndex
)
if ($torchInstall.ExitCode -ne 0) { throw "The supported CPU build of PyTorch could not be installed." }

Write-Host "Installing the pinned Audiobook Studio dependencies..."
$dependencyInstall = Invoke-Python -PythonExe $VenvPython -Arguments @(
    "-m", "pip", "install", "--no-cache-dir", "-r", "requirements.txt"
)
if ($dependencyInstall.ExitCode -ne 0) { throw "Audiobook Studio dependencies could not be installed." }

Write-Host "Validating native libraries in separate clean processes..."
$checks = @(
    @{ Name = "torch"; OCR = $false },
    @{ Name = "onnxruntime"; OCR = $false },
    @{ Name = "rapidocr"; OCR = $true },
    @{ Name = "kokoro"; OCR = $false },
    @{ Name = "pyside6"; OCR = $false },
    @{ Name = "psutil"; OCR = $false }
)
$failed = [System.Collections.Generic.List[string]]::new()
foreach ($check in $checks) {
    $ok = Test-Component -PythonExe $VenvPython -Component $check.Name -InitializeOCR:([bool]$check.OCR)
    if ($ok) {
        Write-Host "[PASS] $($check.Name)" -ForegroundColor Green
    }
    else {
        Write-Host "[FAIL] $($check.Name)" -ForegroundColor Red
        $failed.Add([string]$check.Name)
    }
}

if ($failed.Count -gt 0) {
    throw "The clean runtime still failed: $($failed -join ', '). Review $LogPath. Restart Windows once if the Visual C++ installer returned 3010, then run .\repair_runtime.ps1 -ForceRebuild."
}

$runtimeInfo = Invoke-Python -PythonExe $VenvPython -Arguments @(
    "-c",
    "import json,platform,sys,torch,onnxruntime,rapidocr,kokoro,psutil; print(json.dumps({'python':sys.version.split()[0],'executable':sys.executable,'architecture':platform.architecture()[0],'torch':torch.__version__,'onnxruntime':onnxruntime.__version__,'rapidocr':rapidocr.__version__,'kokoro':getattr(kokoro,'__version__','unknown'),'psutil':psutil.__version__}, indent=2))"
) -CaptureOutput
if ($runtimeInfo.ExitCode -eq 0) {
    $runtimeInfo.StdOut | Set-Content -LiteralPath (Join-Path $ProjectRoot ".runtime_ready.json") -Encoding UTF8
}

Write-RepairLog "Runtime repair completed successfully."
Write-Host ""
Write-Host "[PASS] Audiobook Studio now has an isolated, validated Windows CPU runtime." -ForegroundColor Green
Write-Host "Runtime: $VenvPython"
Write-Host "Next: .\run_phase3_checks.ps1"
