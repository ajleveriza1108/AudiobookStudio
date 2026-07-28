# Audiobook Studio v0.3.0 R1.14.1 Installation

Close Audiobook Studio. Extract `AudiobookStudio-v0.3.0-Update-R1.14.1.zip` into a new folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass

.\install_v030_r1_14_1.ps1 `
    -ProjectRoot "D:\Python\AudiobookStudio"
```

The staged Python tests run offscreen. A small Windows progress window then opens briefly for the real worker-to-GUI dispatch probe. The live project is not changed until both stages pass.

R1.14.1 is cumulative over R1.12 and preserves the verified `.venv` and all user data. After installation, generate the scanned book again so old flattened OCR caches are rebuilt with coordinate-aware reading order.
