# Install Audiobook Studio R1.17.2

Close Audiobook Studio and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_17_2.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

This cumulative update installs the narration-quality repair that
R1.17.1 did not reach. It preserves all runtimes, models, books,
projects, voice samples, generated audio, settings, and Advanced OCR
capability records.
