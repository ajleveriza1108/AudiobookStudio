# Audiobook Studio v0.3.0 R1.14.2

This cumulative update includes structured OCR reading order and the GUI-thread safety repair. It also fixes the Windows preflight that returned `0xC0000374` only after all tests had passed.

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_v030_r1_14_2.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

The existing `.venv`, books, OCR cache, projects, models, voices, output, and local JSON files are preserved.
