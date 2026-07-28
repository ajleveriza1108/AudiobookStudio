# Audiobook Studio v0.3.0 R1.6

## Permanent OCR installer and native-process repair

R1.6 fixes the PowerShell failure that occurred while `install_ocr.ps1` was checking whether RapidOCR was already installed. The old script launched Python directly while `$ErrorActionPreference` was set to `Stop`. A normal Python import traceback from a missing package was converted into a terminating `NativeCommandError`, so the script stopped before it reached `pip install`.

### Repairs

- Adds `Scripts/native_process.ps1`, a Windows PowerShell 5.1-compatible process runner.
- Keeps native stderr separate from PowerShell's error pipeline.
- Preserves numeric exit codes without capturing visible output as the exit code.
- Adds `Scripts/ocr_runtime_check.py` for structured RapidOCR and ONNX Runtime diagnostics.
- Rebuilds `install_ocr.ps1` so a failed import check proceeds to installation instead of terminating.
- Pins RapidOCR to the tested 3.9.2 release.
- Verifies that `RapidOCR()` can initialize, not merely that the packages are present.
- Writes detailed OCR failures to `Logs/ocr_install_YYYYMMDD_HHMMSS.log`.
- Adds an optional `-Repair` mode that reinstalls only the two OCR wheels without replacing the rest of the Python environment.
- Applies the same native-process protection to dependency installation, verification, and application launching.

### Preserved data

The repair does not replace or delete books, models, projects, output, voices, OCR cache, logs, pronunciation rules, or local JSON settings.
