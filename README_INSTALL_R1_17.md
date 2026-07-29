# Install Audiobook Studio R1.17.0

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_17.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

After installation, open **Settings → OCR** and turn on the Advanced OCR toggle.
The app checks and records the laptop first. Unsupported laptops remain on
RapidOCR.

The optional model is installed separately:

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\install_advanced_ocr.ps1
```
