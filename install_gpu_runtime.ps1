param(
    [string]$ProjectRoot = "D:\Python\AudiobookStudio",
    [switch]$ForceRebuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$CpuPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$GpuVenv = Join-Path $ProjectRoot ".gpu-venv"
$GpuPython = Join-Path $GpuVenv "Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$Probe = Join-Path $ProjectRoot "Scripts\gpu_runtime_probe.py"
$Marker = Join-Path $ProjectRoot ".gpu-runtime-ready.json"
$Backup = $null

function Resolve-NvidiaSmiPath {
    # Get-Command returns an ApplicationInfo object in Windows PowerShell 5.1.
    # That object normally exposes Source/Path/Definition, not FullName.
    $Command = Get-Command "nvidia-smi.exe" `
        -CommandType Application `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($Command) {
        foreach ($PropertyName in @("Source", "Path", "Definition")) {
            $Property = $Command.PSObject.Properties[$PropertyName]
            if ($Property) {
                $Candidate = [string]$Property.Value
                if (-not [string]::IsNullOrWhiteSpace($Candidate) -and
                    (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
                    return [System.IO.Path]::GetFullPath($Candidate)
                }
            }
        }
    }

    $Candidates = New-Object System.Collections.Generic.List[string]

    if (-not [string]::IsNullOrWhiteSpace($env:WINDIR)) {
        [void]$Candidates.Add(
            (Join-Path $env:WINDIR "System32\nvidia-smi.exe")
        )
    }
    if (-not [string]::IsNullOrWhiteSpace($env:ProgramW6432)) {
        [void]$Candidates.Add(
            (Join-Path $env:ProgramW6432 "NVIDIA Corporation\NVSMI\nvidia-smi.exe")
        )
    }
    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        [void]$Candidates.Add(
            (Join-Path $env:ProgramFiles "NVIDIA Corporation\NVSMI\nvidia-smi.exe")
        )
    }

    foreach ($Candidate in $Candidates) {
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($Candidate)
        }
    }

    return $null
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Step
    )
    Write-Host $Step
    & $FilePath @Arguments
    $Code = $LASTEXITCODE
    if ($Code -ne 0) {
        throw "$Step failed with exit code $Code."
    }
}

Write-Host "============================================================"
Write-Host "Audiobook Studio RTX 2050 GPU Runtime Installer R1.17.5.2"
Write-Host "Protected automatic hybrid CPU + GPU mode"
Write-Host "============================================================"
Write-Host "Project: $ProjectRoot"

if ($env:OS -ne "Windows_NT") {
    throw "The GPU runtime installer supports Windows only."
}
if (-not (Test-Path -LiteralPath $CpuPython -PathType Leaf)) {
    throw "The protected CPU runtime is missing: $CpuPython"
}
if (-not (Test-Path -LiteralPath $Requirements -PathType Leaf)) {
    throw "requirements.txt is missing: $Requirements"
}
if (-not (Test-Path -LiteralPath $Probe -PathType Leaf)) {
    throw "The GPU probe is missing: $Probe"
}

function Get-NvidiaAdapterName {
    $Names = New-Object System.Collections.Generic.List[string]

    try {
        $Adapters = Get-CimInstance `
            -ClassName Win32_VideoController `
            -ErrorAction Stop
        foreach ($Adapter in $Adapters) {
            $Name = [string]$Adapter.Name
            if (-not [string]::IsNullOrWhiteSpace($Name) -and
                $Name -match "NVIDIA") {
                [void]$Names.Add($Name.Trim())
            }
        }
    }
    catch {
        Write-Host "[WARN] CIM video-adapter query failed: $($_.Exception.Message)" `
            -ForegroundColor Yellow
    }

    if ($Names.Count -eq 0) {
        try {
            $Adapters = Get-WmiObject `
                -Class Win32_VideoController `
                -ErrorAction Stop
            foreach ($Adapter in $Adapters) {
                $Name = [string]$Adapter.Name
                if (-not [string]::IsNullOrWhiteSpace($Name) -and
                    $Name -match "NVIDIA") {
                    [void]$Names.Add($Name.Trim())
                }
            }
        }
        catch {
            Write-Host "[WARN] WMI video-adapter query failed: $($_.Exception.Message)" `
                -ForegroundColor Yellow
        }
    }

    return @($Names | Select-Object -Unique)
}

function ConvertTo-NativeArgumentString {
    param([string[]]$Arguments)

    $Encoded = foreach ($Argument in $Arguments) {
        $Value = [string]$Argument
        if ($Value -match '[\s"]') {
            '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
        }
        else {
            $Value
        }
    }
    return ($Encoded -join " ")
}

function Invoke-NativeCapture {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    $StartInfo = New-Object System.Diagnostics.ProcessStartInfo
    $StartInfo.FileName = $FilePath
    $StartInfo.Arguments = ConvertTo-NativeArgumentString -Arguments $Arguments
    $StartInfo.UseShellExecute = $false
    $StartInfo.RedirectStandardOutput = $true
    $StartInfo.RedirectStandardError = $true
    $StartInfo.CreateNoWindow = $true

    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $StartInfo

    if (-not $Process.Start()) {
        throw "Could not start native process: $FilePath"
    }

    $StandardOutput = $Process.StandardOutput.ReadToEnd()
    $StandardError = $Process.StandardError.ReadToEnd()
    $Process.WaitForExit()

    return [pscustomobject]@{
        ExitCode = [int]$Process.ExitCode
        StandardOutput = [string]$StandardOutput
        StandardError = [string]$StandardError
    }
}

Write-Host "[1/8] Detecting the NVIDIA laptop GPU..."
$AdapterNames = @(Get-NvidiaAdapterName)
$DetectedAdapter = $AdapterNames |
    Where-Object { $_ -match "RTX\s*2050" } |
    Select-Object -First 1

if ([string]::IsNullOrWhiteSpace([string]$DetectedAdapter)) {
    if ($AdapterNames.Count -gt 0) {
        throw "This focused installer requires an NVIDIA GeForce RTX 2050. Detected NVIDIA adapter(s): $($AdapterNames -join ', ')"
    }
    throw "Windows did not report an NVIDIA GeForce RTX 2050 display adapter. Verify the NVIDIA driver in Device Manager."
}

Write-Host "Windows adapter: $DetectedAdapter"
Write-Host "[PASS] NVIDIA GeForce RTX 2050 detected by Windows."

$NvidiaSmiPath = Resolve-NvidiaSmiPath
if ([string]::IsNullOrWhiteSpace($NvidiaSmiPath)) {
    Write-Host "[WARN] nvidia-smi.exe was not found. The real PyTorch CUDA test will be the final compatibility gate." `
        -ForegroundColor Yellow
}
else {
    Write-Host "nvidia-smi: $NvidiaSmiPath"
    try {
        $SmiResult = Invoke-NativeCapture `
            -FilePath $NvidiaSmiPath `
            -Arguments @(
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader,nounits"
            )

        if ($SmiResult.ExitCode -eq 0 -and
            -not [string]::IsNullOrWhiteSpace($SmiResult.StandardOutput)) {
            $SmiLine = ($SmiResult.StandardOutput -split "\r?\n" |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                Select-Object -First 1).Trim()
            Write-Host "NVIDIA driver query: $SmiLine"
        }
        else {
            Write-Host "[WARN] nvidia-smi diagnostic query was unavailable and will not block installation." `
                -ForegroundColor Yellow
            Write-Host "       Exit code: $($SmiResult.ExitCode)"
            if (-not [string]::IsNullOrWhiteSpace($SmiResult.StandardError)) {
                Write-Host "       $($SmiResult.StandardError.Trim())"
            }
        }
    }
    catch {
        Write-Host "[WARN] nvidia-smi diagnostic query failed and will not block installation: $($_.Exception.Message)" `
            -ForegroundColor Yellow
    }
}

Write-Host "[INFO] The post-install PyTorch CUDA tensor test is the authoritative GPU gate."

Write-Host "[2/8] Checking free storage..."
$DriveRoot = [System.IO.Path]::GetPathRoot($ProjectRoot)
$Drive = Get-PSDrive -Name $DriveRoot.Substring(0, 1)
$FreeGB = [math]::Round($Drive.Free / 1GB, 2)
Write-Host "Free space: $FreeGB GB"
if ($Drive.Free -lt 10GB) {
    throw "At least 10 GB of free space is required to build the isolated GPU runtime."
}
Write-Host "[PASS] Storage check passed."

if ((Test-Path -LiteralPath $GpuPython -PathType Leaf) -and -not $ForceRebuild) {
    Write-Host "[3/8] Testing the existing GPU runtime..."
    & $GpuPython -u $Probe `
        --project-root $ProjectRoot `
        --require-name "RTX 2050"
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[PASS] The existing RTX 2050 runtime is already ready." -ForegroundColor Green
        return
    }
    Write-Host "[INFO] Existing GPU runtime failed verification and will be rebuilt."
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path -LiteralPath $GpuVenv) {
    $Backup = Join-Path $ProjectRoot (".gpu-venv.previous_{0}" -f $Stamp)
    Move-Item -LiteralPath $GpuVenv -Destination $Backup
}
Remove-Item -LiteralPath $Marker -Force -ErrorAction SilentlyContinue

try {
    Write-Host "[3/8] Creating the isolated GPU runtime..."
    Invoke-Checked -FilePath $CpuPython -Arguments @(
        "-m", "venv", $GpuVenv
    ) -Step "Creating .gpu-venv"
    if (-not (Test-Path -LiteralPath $GpuPython -PathType Leaf)) {
        throw "The GPU Python executable was not created."
    }

    Write-Host "[4/8] Updating GPU-runtime packaging tools..."
    Invoke-Checked -FilePath $GpuPython -Arguments @(
        "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"
    ) -Step "Updating pip, setuptools, and wheel"

    Write-Host "[5/8] Installing the pinned PyTorch 2.6.0 CUDA 12.4 wheel..."
    Invoke-Checked -FilePath $GpuPython -Arguments @(
        "-m", "pip", "install",
        "torch==2.6.0",
        "--index-url", "https://download.pytorch.org/whl/cu124"
    ) -Step "Installing CUDA-enabled PyTorch"

    Write-Host "[6/8] Installing the verified Audiobook Studio dependencies..."
    Invoke-Checked -FilePath $GpuPython -Arguments @(
        "-m", "pip", "install", "-r", $Requirements
    ) -Step "Installing application dependencies"

    Write-Host "[7/8] Running a real RTX 2050 CUDA tensor test..."
    Invoke-Checked -FilePath $GpuPython -Arguments @(
        "-u", $Probe,
        "--project-root", $ProjectRoot,
        "--require-name", "RTX 2050"
    ) -Step "Verifying CUDA, Kokoro dependencies, and GUI dependencies"

    Write-Host "[8/8] Running the exact compact GUI construction test..."
    Invoke-Checked -FilePath $GpuPython -Arguments @(
        (Join-Path $ProjectRoot "Scripts\compact_gui_smoke.py")
    ) -Step "Verifying the PySide6 GUI in .gpu-venv"

    if ($Backup -and (Test-Path -LiteralPath $Backup)) {
        Remove-Item -LiteralPath $Backup -Recurse -Force
    }

    Write-Host ""
    Write-Host "[PASS] RTX 2050 automatic GPU acceleration is installed." -ForegroundColor Green
    Write-Host "GPU runtime: $GpuPython"
    Write-Host "Stable CPU fallback preserved: $CpuPython"
    Write-Host ""
    Write-Host "Automatic work assignment:"
    Write-Host "  - Kokoro narration: RTX 2050 CUDA"
    Write-Host "  - PDF loading, text processing, RapidOCR, and audio assembly: CPU"
    Write-Host "  - Advanced Unlimited-OCR: remains separate and disabled unless explicitly installed"
    Write-Host ""
    Write-Host "Launch normally: .\LAUNCH_AUDIOBOOK_STUDIO.bat"
}
catch {
    Write-Host ""
    Write-Host "[FAIL] GPU runtime installation failed." -ForegroundColor Red
    Write-Host $_.Exception.Message

    if (Test-Path -LiteralPath $GpuVenv) {
        Remove-Item -LiteralPath $GpuVenv -Recurse -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $Marker -Force -ErrorAction SilentlyContinue

    if ($Backup -and (Test-Path -LiteralPath $Backup)) {
        Move-Item -LiteralPath $Backup -Destination $GpuVenv
        Write-Host "[RESTORED] The previous GPU runtime was restored."
    }

    Write-Host "[SAFE] The protected CPU runtime was not modified."
    throw
}
