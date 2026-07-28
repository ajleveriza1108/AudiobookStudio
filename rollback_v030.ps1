[CmdletBinding()]
param(
    [string]$ProjectRoot = "D:\Python\AudiobookStudio",
    [Parameter(Mandatory = $true)]
    [string]$BackupRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$BackupRoot = [System.IO.Path]::GetFullPath($BackupRoot)

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project folder not found: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $BackupRoot -PathType Container)) {
    throw "Backup folder not found: $BackupRoot"
}

$newFilesManifest = Join-Path $BackupRoot "_v030_new_files.txt"
if (Test-Path -LiteralPath $newFilesManifest -PathType Leaf) {
    $newFiles = @(Get-Content -LiteralPath $newFilesManifest -Encoding UTF8 | Where-Object { $_.Trim() })
    [array]::Reverse($newFiles)
    foreach ($relativeForward in $newFiles) {
        $relative = $relativeForward.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
        $target = Join-Path $ProjectRoot $relative
        if (Test-Path -LiteralPath $target -PathType Leaf) {
            Remove-Item -LiteralPath $target -Force
            Write-Host "Removed new file: $relativeForward"
        }
    }
}

Get-ChildItem -LiteralPath $BackupRoot -File -Recurse | Where-Object {
    $_.Name -notin @("_v030_new_files.txt", "_v030_backup_manifest.txt")
} | ForEach-Object {
    $relative = $_.FullName.Substring($BackupRoot.Length).TrimStart('\', '/')
    $destination = Join-Path $ProjectRoot $relative
    $parent = Split-Path -Parent $destination
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    Write-Host "Restored: $relative"
}

foreach ($rootName in @("core", "ui", "controllers", "workers", "engines", "tests", "Scripts")) {
    $root = Join-Path $ProjectRoot $rootName
    if (Test-Path -LiteralPath $root) {
        Get-ChildItem -LiteralPath $root -Directory -Filter "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }
}
foreach ($cache in @("__pycache__", ".pytest_cache")) {
    $path = Join-Path $ProjectRoot $cache
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "[PASS] Audiobook Studio rollback completed." -ForegroundColor Green
Write-Host "Project: $ProjectRoot"
Write-Host "Backup:  $BackupRoot"
