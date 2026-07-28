# Audiobook Studio v0.3.0 Alpha R1.7

## Permanent Windows native-runtime repair

R1.6 proved that RapidOCR could initialize in its own process, while the full
verification later reported failures for both PyTorch and ONNX Runtime. The
project was still using a heavily populated system Python installation. A
failed PyTorch native import could also contaminate later native imports in the
same verification process.

R1.7 makes the following permanent changes:

- Audiobook Studio now uses only `D:\Python\AudiobookStudio\.venv` at runtime.
- The launcher and verifier no longer fall back to system site-packages.
- The Microsoft Visual C++ 2015-2022 x64 runtime is installed or repaired from
  Microsoft's official stable URL.
- PyTorch 2.6.0 CPU is installed from PyTorch's official CPU wheel index.
- ONNX Runtime is pinned to 1.22.1 instead of accepting future native builds.
- Kokoro and RapidOCR remain pinned to their tested releases.
- PyTorch, ONNX Runtime, RapidOCR, Kokoro, and PySide6 are validated in
  separate Python processes so one failed DLL import cannot poison another.
- A real tensor operation and OCR-engine initialization are required before the
  runtime is declared ready.
- The global Python installation is no longer modified or trusted by the app.

## Main repair command

```powershell
Set-Location "D:\Python\AudiobookStudio"
.\repair_runtime.ps1 -ForceRebuild
.\run_phase3_checks.ps1
.\LAUNCH_AUDIOBOOK_STUDIO.bat
```
