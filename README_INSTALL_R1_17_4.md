# Install Audiobook Studio R1.17.4

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_17_4.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

R1.17.4 preserves the runtime, books, projects, models, outputs, and the gold
reference WAV. It invalidates only old OCR caches whose correction-profile
identity is no longer current.
