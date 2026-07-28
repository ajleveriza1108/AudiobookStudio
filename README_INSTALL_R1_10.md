# Audiobook Studio v0.3.0 Update R1.10

R1.9 was rolled back safely because `PySide6==6.8.7` does not exist for this
Python 3.12 installation. R1.10 uses the published `PySide6==6.8.3` wheel and
applies the native Windows paint repair.

Install from a newly extracted folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_v030_r1_10.ps1 -ProjectRoot "D:\Python\AudiobookStudio"
```

The installer keeps the existing `.venv` and changes only the PySide6/Qt GUI
wheel set plus the paint-safe application files. A real application window will
open briefly and close automatically during verification.
