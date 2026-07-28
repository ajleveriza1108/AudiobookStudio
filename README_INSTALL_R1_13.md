# Audiobook Studio v0.3.0 R1.13 Installation

Close Audiobook Studio, extract the R1.13 update into a new folder, and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_v030_r1_13.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

R1.13 does not rebuild the project runtime. It repairs worker-to-GUI thread dispatch and runs
a visible Windows stress probe that sends thousands of queued progress updates.

After installation:

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```
