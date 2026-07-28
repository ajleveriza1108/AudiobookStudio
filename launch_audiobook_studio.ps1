param(
    [switch]$NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$repairHint = ".\run_phase3_checks.ps1"

$env:PYTHONNOUSERSITE = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:CUDA_VISIBLE_DEVICES = ""
$env:AUDIOBOOK_STUDIO_DEVICE = "cpu"
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

try {
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        $repairHint = ".\repair_runtime.ps1 -ForceRebuild"
        throw "The dedicated runtime is missing."
    }

    & $VenvPython -u "Scripts\runtime_health.py" --component torch *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = ".\repair_runtime.ps1 -ForceRebuild"
        throw "PyTorch native libraries are not healthy."
    }
    & $VenvPython -u "Scripts\runtime_health.py" --component onnxruntime *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = ".\repair_runtime.ps1 -ForceRebuild"
        throw "ONNX Runtime native libraries are not healthy."
    }
    & $VenvPython -u "Scripts\runtime_health.py" --component psutil *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = ".\install_dependencies.ps1"
        throw "The system-monitor dependency is unavailable."
    }
    & $VenvPython -u "Scripts\runtime_health.py" --component pyside6 *> $null
    if ($LASTEXITCODE -ne 0) {
        $repairHint = ".\repair_gui_runtime.ps1"
        throw "The tested Qt/PySide GUI runtime is unavailable."
    }

    & $VenvPython -u "app.py"
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
    Write-Host "Repair: $repairHint"
    Write-Host "Safe Start will avoid reopening the previous book after an unclean exit."
    if (-not $NoPause) { Read-Host "Press Enter to close" }
    exit 1
}

exit 0
