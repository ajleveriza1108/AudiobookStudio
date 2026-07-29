param(
    [string]$ProjectRoot = "D:\Python\AudiobookStudio"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$GpuVenv = Join-Path $ProjectRoot ".gpu-venv"
$Marker = Join-Path $ProjectRoot ".gpu-runtime-ready.json"

if (Test-Path -LiteralPath $GpuVenv) {
    Remove-Item -LiteralPath $GpuVenv -Recurse -Force
}
Remove-Item -LiteralPath $Marker -Force -ErrorAction SilentlyContinue

Write-Host "[PASS] The optional GPU runtime was removed."
Write-Host "[PASS] Audiobook Studio will automatically use the protected CPU runtime."
