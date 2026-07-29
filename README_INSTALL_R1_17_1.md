# Install Audiobook Studio R1.17.1

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_17_1.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

The installer preserves `.venv`, `.advanced-ocr-venv`, books, models, projects,
voice samples, generated audio, configuration, and all existing user data.
