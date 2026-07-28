# Install Audiobook Studio v0.3.0 R1.12

R1.12 is a small source-only repair. It keeps the already verified project-local
runtime and PySide6 6.8.3 installation.

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_12.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

The installer first creates a staged copy and runs the exact two tests that
blocked R1.11. It does not touch the live source until that preflight passes.
It then installs the R1.11 stability changes plus the compatibility repair and
runs the full real-Windows verification.

After success:

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```

Do not rebuild the AI/OCR runtime and do not reinstall PySide6.
