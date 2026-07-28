# Install R1.16

Close Audiobook Studio, extract the R1.16 update into a new folder, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_16.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

Launch afterward:

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```

The optional Voice Studio engine is installed separately from **Tools > Voice Studio**, or with:

```powershell
.\install_voice_cloning.ps1
```

The optional installer requires Python 3.11 x64 and creates `.voice-venv`. It does not change the verified `.venv` used by Kokoro and OCR.
