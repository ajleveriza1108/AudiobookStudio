# Install Audiobook Studio R1.16.2

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_16_2.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

This focused update preserves `.venv`, books, models, projects,
generated audio, voices, OCR cache, and local settings.
