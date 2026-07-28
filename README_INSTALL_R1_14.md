# Install Audiobook Studio R1.14

Close Audiobook Studio, extract the R1.14 update into a new folder, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_14.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

R1.14 preserves the existing `.venv`, books, models, projects, output, voices, local settings, pronunciation rules, and OCR source files.

After installation:

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```

Import the scanned book and generate it again. The older flattened OCR cache will be rejected automatically. The project output will include `OCR Reading Order Report.json` for inspection.
