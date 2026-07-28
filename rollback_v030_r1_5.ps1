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

if (-not (Test-Path -LiteralPath $BackupRoot -PathType Container)) {
    throw "Backup folder not found: $BackupRoot"
}

$newFilesList = Join-Path $BackupRoot "_r15_new_files.txt"
if (Test-Path -LiteralPath $newFilesList) {
    foreach ($relativeForward in Get-Content -LiteralPath $newFilesList -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($relativeForward)) { continue }
        $relative = $relativeForward.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
        $target = Join-Path $ProjectRoot $relative
        if (Test-Path -LiteralPath $target -PathType Leaf) {
            Remove-Item -LiteralPath $target -Force
        }
    }
}

Get-ChildItem -LiteralPath $BackupRoot -File -Recurse | Where-Object {
    $_.Name -notin @("_r15_new_files.txt", "_r15_backup_manifest.txt")
} | ForEach-Object {
    $relative = $_.FullName.Substring($BackupRoot.Length).TrimStart([char[]]@('\', '/'))
    $destination = Join-Path $ProjectRoot $relative
    $parent = Split-Path -Parent $destination
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
}

Get-ChildItem -LiteralPath $ProjectRoot -Directory -Filter "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[PASS] R1.5 rollback completed." -ForegroundColor Green
Write-Host "Restored from: $BackupRoot"
