# Install Audiobook Studio v0.3.0 R1.11

R1.11 is a focused source repair. It keeps the verified R1.10 PySide6 6.8.3,
AI, OCR, and FFmpeg runtime. It does not redownload the large environment.

1. Close Audiobook Studio.
2. Extract the R1.11 update into a new folder.
3. Open Windows PowerShell in that folder.
4. Run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_11.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

The real Windows verification window will restore the previous book, remain
visible for at least eight seconds after restoration, and close automatically.

Then launch:

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```

After the preceding crash, the first R1.11 launch intentionally uses Safe
Start: the previous book remains in Library but is not opened automatically.
Select it manually. After a normal close, automatic last-book restoration is
re-enabled for the next launch.
