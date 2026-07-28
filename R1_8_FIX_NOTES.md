# Audiobook Studio v0.3.0 R1.8 — Direct Dependency Contract Repair

R1.7 successfully created the isolated Windows runtime and passed the native
checks for PyTorch, ONNX Runtime, RapidOCR, Kokoro, and PySide6. Full GUI
verification then stopped because the application imports `psutil`, but R1.7
had not declared or installed it.

R1.8 permanently repairs that dependency contract:

- Adds `psutil` as a direct required dependency.
- Adds `requests` as a direct dependency because the update checker imports it.
- Verifies psutil before constructing the GUI.
- Performs real CPU and memory metric calls in the runtime health checker.
- Adds psutil to normal runtime repair and launcher preflight checks.
- Installs only the two missing direct dependencies into the existing `.venv`;
  the large PyTorch, PySide6, OCR, and Kokoro packages are not rebuilt.
- Adds regression tests so source imports cannot silently drift away from the
  declared runtime dependencies again.

The user's Books, Cache, Logs, Models, Output, Projects, Temp, Voices, local
configuration, pronunciation rules, and existing `.venv` are preserved.
