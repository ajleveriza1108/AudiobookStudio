param(
    [switch]$NoPause,
    [ValidateSet("auto", "gpu", "cpu")]
    [string]$Device = "auto"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

$CpuPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$GpuPython = Join-Path $ProjectRoot ".gpu-venv\Scripts\python.exe"
$GpuMarker = Join-Path $ProjectRoot ".gpu-runtime-ready.json"
$GpuProbe = Join-Path $ProjectRoot "Scripts\gpu_runtime_probe.py"
$repairHint = ".\run_phase3_checks.ps1"

$env:PYTHONNOUSERSITE = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:CUDA_DEVICE_ORDER = "PCI_BUS_ID"

# Keep the verified Qt software-rendering repair. CUDA remains available for
# Kokoro and supported AI inference; the GUI itself does not consume VRAM.
$env:QT_STYLE_OVERRIDE = "Fusion"
$env:QT_OPENGL = "software"
$env:QT_QUICK_BACKEND = "software"
$env:QSG_RHI_BACKEND = "software"
$env:QT_WIDGETS_RHI = "0"

if ($env:OS -eq "Windows_NT") {
    $windowsFonts = Join-Path $env:WINDIR "Fonts"
    if (Test-Path -LiteralPath $windowsFonts) {
        $env:QT_QPA_FONTDIR = $windowsFonts
    }
}

function Test-GpuRuntime {
    if (-not (Test-Path -LiteralPath $GpuPython -PathType Leaf)) {
        return $false
    }
    if (-not (Test-Path -LiteralPath $GpuMarker -PathType Leaf)) {
        return $false
    }
    if (-not (Test-Path -LiteralPath $GpuProbe -PathType Leaf)) {
        return $false
    }

    & $GpuPython -u $GpuProbe `
        --project-root $ProjectRoot `
        --require-name "RTX 2050" `
        --quiet
    return ($LASTEXITCODE -eq 0)
}

try {
    if (-not (Test-Path -LiteralPath $CpuPython -PathType Leaf)) {
        $repairHint = ".\repair_runtime.ps1 -ForceRebuild"
        throw "The stable CPU runtime is missing."
    }

    $RuntimePython = $CpuPython
    $Backend = "CPU fallback"
    $UseGpu = $false

    if ($Device -ne "cpu") {
        $UseGpu = Test-GpuRuntime
    }

    if ($UseGpu) {
        $RuntimePython = $GpuPython
        $Backend = "NVIDIA GeForce RTX 2050"
        $env:AUDIOBOOK_STUDIO_DEVICE = "cuda"
        $env:AUDIOBOOK_STUDIO_ALLOW_CPU_FALLBACK = "1"
        $env:CUDA_VISIBLE_DEVICES = "0"
        Write-Host "[BACKEND] Automatic hybrid mode enabled." -ForegroundColor Green
        Write-Host "[BACKEND] Kokoro narration: NVIDIA GeForce RTX 2050"
        Write-Host "[BACKEND] PDF, text preparation, standard OCR, and audio assembly: CPU"
    }
    else {
        if ($Device -eq "gpu") {
            $repairHint = ".\install_gpu_runtime.ps1 -ProjectRoot `"$ProjectRoot`""
            throw "The RTX 2050 runtime is not ready or did not pass its CUDA execution test."
        }
        $RuntimePython = $CpuPython
        $env:AUDIOBOOK_STUDIO_DEVICE = "cpu"
        $env:AUDIOBOOK_STUDIO_ALLOW_CPU_FALLBACK = "1"
        Remove-Item Env:CUDA_VISIBLE_DEVICES -ErrorAction SilentlyContinue
        Write-Host "[BACKEND] GPU runtime unavailable; using the protected CPU runtime." -ForegroundColor Yellow
        Write-Host "[BACKEND] Repair/install GPU runtime: .\install_gpu_runtime.ps1 -ProjectRoot `"$ProjectRoot`""
    }

    & $RuntimePython -u "Scripts\runtime_health.py" --component torch *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = if ($UseGpu) {
            ".\install_gpu_runtime.ps1 -ProjectRoot `"$ProjectRoot`""
        } else {
            ".\repair_runtime.ps1 -ForceRebuild"
        }
        throw "PyTorch native libraries are not healthy in the selected runtime."
    }

    & $RuntimePython -u "Scripts\runtime_health.py" --component onnxruntime *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = if ($UseGpu) {
            ".\install_gpu_runtime.ps1 -ProjectRoot `"$ProjectRoot`""
        } else {
            ".\repair_runtime.ps1 -ForceRebuild"
        }
        throw "ONNX Runtime native libraries are not healthy in the selected runtime."
    }

    & $RuntimePython -u "Scripts\runtime_health.py" --component psutil *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = ".\install_dependencies.ps1"
        throw "The system-monitor dependency is unavailable."
    }

    & $RuntimePython -u "Scripts\runtime_health.py" --component pyside6 *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = if ($UseGpu) {
            ".\install_gpu_runtime.ps1 -ProjectRoot `"$ProjectRoot`""
        } else {
            ".\repair_gui_runtime.ps1"
        }
        throw "The tested Qt/PySide GUI runtime is unavailable."
    }

    & $RuntimePython -u "app.py"
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        if ($code -eq -1073741819) {
            $repairHint = "Review Logs\native_crash.log; do not rebuild the verified AI runtime."
            throw "A native access violation occurred. The crash log identifies the exact thread and callback."
        }
        throw "Audiobook Studio exited with code $code."
    }
}
catch {
    Write-Host ""
    Write-Host "Audiobook Studio could not start." -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Startup stage: $ProjectRoot\Logs\startup_stage.json"
    Write-Host "Native crash details: $ProjectRoot\Logs\native_crash.log"
    Write-Host "GPU status: $ProjectRoot\Logs\gpu_runtime_status.json"
    Write-Host "Repair: $repairHint"
    Write-Host "Safe Start will avoid reopening the previous book after an unclean exit."
    if (-not $NoPause) { Read-Host "Press Enter to close" }
    exit 1
}

exit 0
