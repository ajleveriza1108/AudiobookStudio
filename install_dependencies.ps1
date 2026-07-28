[CmdletBinding()]
param(
    [switch]$ForceRebuild,
    [switch]$SkipVCRuntime
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repair = Join-Path $PSScriptRoot "repair_runtime.ps1"
if (-not (Test-Path -LiteralPath $repair -PathType Leaf)) {
    throw "The runtime repair script is missing: $repair"
}
& $repair -ForceRebuild:$ForceRebuild -SkipVCRuntime:$SkipVCRuntime
exit $LASTEXITCODE
