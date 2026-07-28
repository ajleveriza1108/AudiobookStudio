Set-StrictMode -Version Latest

function ConvertTo-NativeArgument {
    param(
        [AllowEmptyString()]
        [string]$Value
    )

    if ($null -eq $Value -or $Value.Length -eq 0) {
        return '""'
    }
    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append('"')
    $backslashes = 0

    foreach ($character in $Value.ToCharArray()) {
        if ([int][char]$character -eq 92) {
            $backslashes++
            continue
        }

        if ($character -eq '"') {
            if ($backslashes -gt 0) {
                [void]$builder.Append(((1..($backslashes * 2) | ForEach-Object { [char]92 }) -join ''))
                $backslashes = 0
            }
            [void]$builder.Append('\"')
            continue
        }

        if ($backslashes -gt 0) {
            [void]$builder.Append(((1..$backslashes | ForEach-Object { [char]92 }) -join ''))
            $backslashes = 0
        }
        [void]$builder.Append($character)
    }

    if ($backslashes -gt 0) {
        [void]$builder.Append(((1..($backslashes * 2) | ForEach-Object { [char]92 }) -join ''))
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Invoke-NativeProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [string[]]$Arguments = @(),

        [string]$WorkingDirectory = (Get-Location).Path,

        [switch]$CaptureOutput,

        [switch]$ShowCapturedOutput,

        [string]$LogPath
    )

    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $FilePath
    $processInfo.Arguments = (($Arguments | ForEach-Object { ConvertTo-NativeArgument -Value ([string]$_) }) -join ' ')
    $processInfo.WorkingDirectory = $WorkingDirectory
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $false
    $processInfo.RedirectStandardOutput = [bool]$CaptureOutput
    $processInfo.RedirectStandardError = [bool]$CaptureOutput

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo

    try {
        if (-not $process.Start()) {
            throw "The process could not be started: $FilePath"
        }

        $standardOutput = ''
        $standardError = ''
        if ($CaptureOutput) {
            $stdoutTask = $process.StandardOutput.ReadToEndAsync()
            $stderrTask = $process.StandardError.ReadToEndAsync()
            $process.WaitForExit()
            $standardOutput = $stdoutTask.Result
            $standardError = $stderrTask.Result
        }
        else {
            $process.WaitForExit()
        }

        if ($LogPath) {
            $parent = Split-Path -Parent $LogPath
            if ($parent) {
                New-Item -ItemType Directory -Force -Path $parent | Out-Null
            }
            $logLines = @(
                "Command: $FilePath $($processInfo.Arguments)",
                "Exit code: $($process.ExitCode)",
                '',
                'STDOUT:',
                $standardOutput,
                '',
                'STDERR:',
                $standardError
            )
            $logLines | Set-Content -LiteralPath $LogPath -Encoding UTF8
        }

        if ($CaptureOutput -and $ShowCapturedOutput) {
            if (-not [string]::IsNullOrWhiteSpace($standardOutput)) {
                Write-Host ($standardOutput.TrimEnd())
            }
            if (-not [string]::IsNullOrWhiteSpace($standardError)) {
                Write-Host ($standardError.TrimEnd()) -ForegroundColor Red
            }
        }

        return [pscustomobject]@{
            ExitCode = [int]$process.ExitCode
            StdOut = [string]$standardOutput
            StdErr = [string]$standardError
            CommandLine = "$FilePath $($processInfo.Arguments)"
        }
    }
    finally {
        $process.Dispose()
    }
}
