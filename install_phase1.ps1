param(
    [string]$ProjectRoot = "D:\Python\AudiobookStudio"
)

$ErrorActionPreference = "Stop"

$SourceRoot = Join-Path $PSScriptRoot "replacement_files"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)

if (-not (Test-Path $SourceRoot)) {
    throw "Replacement files were not found: $SourceRoot"
}

if (-not (Test-Path $ProjectRoot)) {
    throw "AudiobookStudio folder was not found: $ProjectRoot"
}

if (-not (Test-Path (Join-Path $ProjectRoot "app.py"))) {
    throw "This does not look like the AudiobookStudio project: $ProjectRoot"
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "_backup_phase1_$Timestamp"
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

# Preserve private settings before config.json and library.json are sanitized.
$OldConfig = Join-Path $ProjectRoot "config.json"
$LocalConfig = Join-Path $ProjectRoot "config.local.json"
if ((Test-Path $OldConfig) -and -not (Test-Path $LocalConfig)) {
    Copy-Item $OldConfig $LocalConfig
}

$OldLibrary = Join-Path $ProjectRoot "library.json"
$LocalLibrary = Join-Path $ProjectRoot "library.local.json"
if ((Test-Path $OldLibrary) -and -not (Test-Path $LocalLibrary)) {
    Copy-Item $OldLibrary $LocalLibrary
}

Get-ChildItem -Path $SourceRoot -Recurse -File | ForEach-Object {
    $Relative = $_.FullName.Substring($SourceRoot.Length).TrimStart("\", "/")
    $Destination = Join-Path $ProjectRoot $Relative
    $DestinationFolder = Split-Path $Destination -Parent

    New-Item -ItemType Directory -Force -Path $DestinationFolder | Out-Null

    if (Test-Path $Destination) {
        $BackupDestination = Join-Path $BackupRoot $Relative
        $BackupFolder = Split-Path $BackupDestination -Parent
        New-Item -ItemType Directory -Force -Path $BackupFolder | Out-Null
        Copy-Item $Destination $BackupDestination -Force
    }

    Copy-Item $_.FullName $Destination -Force
    Write-Host "Updated: $Relative"
}

Write-Host ""
Write-Host "Phase 1 files installed successfully." -ForegroundColor Green
Write-Host "Project: $ProjectRoot"
Write-Host "Backup:  $BackupRoot"
Write-Host ""
Write-Host "Next commands:"
Write-Host "  cd `"$ProjectRoot`""
Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
Write-Host "  .\.venv\Scripts\python.exe verify_phase1.py"
Write-Host "  .\.venv\Scripts\python.exe app.py"
