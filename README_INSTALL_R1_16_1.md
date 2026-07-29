# Install Audiobook Studio R1.16.1

Close Audiobook Studio, extract the update into a new folder, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_v030_r1_16_1.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

The installer preserves `.venv`, books, projects, models, voices, output,
cache, logs, and private JSON files. It validates the exact SettingsPanel
startup path after installation and rolls back automatically if it fails.
