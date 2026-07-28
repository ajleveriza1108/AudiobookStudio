# Audiobook Studio R1.7 installation

R1.7 replaces use of the shared system Python packages with a dedicated
project-local runtime at `.venv`.

## Install or repair

Open PowerShell in `D:\Python\AudiobookStudio`:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\repair_runtime.ps1 -ForceRebuild
.\run_phase3_checks.ps1
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```

The runtime repair may show a Windows UAC prompt while installing or repairing
the official Microsoft Visual C++ 2015-2022 x64 runtime.

The repair does not alter Books, Projects, Models, Output, Voices, OCR cache,
pronunciation rules, or local settings.
