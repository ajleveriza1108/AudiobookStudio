param(
    [string]$ProjectRoot = $PSScriptRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Checker = Join-Path $ProjectRoot "Scripts\advanced_ocr_capability.py"

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "Audiobook Studio runtime is missing: $PythonExe"
}
if (-not (Test-Path -LiteralPath $Checker -PathType Leaf)) {
    throw "Advanced OCR capability checker is missing: $Checker"
}

& $PythonExe -u $Checker
$Code = $LASTEXITCODE
Write-Host ""
Write-Host "Report: $(Join-Path $ProjectRoot 'Logs\advanced_ocr_capability.json')"
if ($Code -eq 0) {
    Write-Host "[SUPPORTED] This laptop meets the supported Advanced OCR target." -ForegroundColor Green
    exit 0
}
if ($Code -eq 3) {
    Write-Host "[EXPERIMENTAL] This laptop is below the supported target but may run one page at a time." -ForegroundColor Yellow
    exit 3
}
Write-Host "[UNSUPPORTED] Keep Advanced OCR disabled and use RapidOCR." -ForegroundColor Red
exit 4
