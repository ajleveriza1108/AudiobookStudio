param(
    [string]$ProjectRoot = "D:\Python\AudiobookStudio"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$GpuPython = Join-Path $ProjectRoot ".gpu-venv\Scripts\python.exe"
$Probe = Join-Path $ProjectRoot "Scripts\gpu_runtime_probe.py"

if (-not (Test-Path -LiteralPath $GpuPython -PathType Leaf)) {
    throw "The isolated GPU runtime is not installed. Run install_gpu_runtime.ps1."
}

& $GpuPython -u $Probe `
    --project-root $ProjectRoot `
    --require-name "RTX 2050"
if ($LASTEXITCODE -ne 0) {
    throw "The RTX 2050 CUDA runtime did not pass verification."
}
