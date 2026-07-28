# Audiobook Studio v0.3.0 R1.14.3

This cumulative update includes the structured OCR reading-order repair, queued GUI-thread callbacks, and the final QThread preflight cleanup correction.

Install from a newly extracted folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_v030_r1_14_3.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

The existing `.venv`, books, OCR cache, projects, models, voices, output, and local JSON files are preserved. No runtime rebuild is performed.
