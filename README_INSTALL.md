# Audiobook Studio v0.3.0 R1.16

R1.16 is a cumulative source update that keeps the existing Kokoro, OCR, book, project, resume, and export workflow while adding the compact responsive interface and authorized Voice Studio foundation.

Use the separate **AudiobookStudio-v0.3.0-Update-R1.16** package for an existing installation:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_16.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

The installer preserves `.venv`, books, OCR cache, projects, models, voices, output, and local JSON files. The optional voice-cloning module is installed separately and never modifies the verified Kokoro/OCR runtime.
