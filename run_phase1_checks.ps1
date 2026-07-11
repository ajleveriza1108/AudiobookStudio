param(
    [string]$ProjectRoot = "D:\Python\AudiobookStudio"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Virtual environment Python was not found: $Python"
}

& $Python verify_phase1.py
& $Python -m pytest -q
& $Python test_engine.py --list
