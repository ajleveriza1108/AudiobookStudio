# Audiobook Studio v0.3.0 R1.14.1

## Staged Preflight Process Repair

R1.14's structured OCR tests passed, but its package-level preflight launched the Qt dispatch probe with the offscreen platform and propagated an abnormal child-process status directly through `SystemExit`. On Windows that could be reduced to `-1`, hiding the actual child result and stopping before the live project was changed.

R1.14.1 keeps the R1.13 GUI-thread repair and R1.14 coordinate-aware OCR unchanged, while repairing the installer gate:

- Runs unit and OCR tests with Qt's offscreen platform.
- Runs the worker-to-GUI dispatch stress probe separately on the real Windows renderer.
- Removes `QT_QPA_PLATFORM=offscreen` for that native probe.
- Uses software OpenGL/RHI settings for predictable Windows rendering.
- Captures stdout, stderr, signed return code, and hexadecimal Windows status.
- Converts abnormal native child statuses into a normal installer failure code after printing the real diagnosis.
- Never changes the live source until the staged tests and native probe both pass.
- Preserves the existing `.venv`, PySide6 6.8.3, PyTorch, Kokoro, OCR, FFmpeg, books, projects, models, voices, output, and local settings.
