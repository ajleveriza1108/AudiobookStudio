# Audiobook Studio v0.3.0 R1.10 — Published Qt Wheel and Native Paint Repair

R1.9 did not reach installation because it requested `PySide6==6.8.7`, a
version that is not published for the user's Python 3.12 environment. The pip
resolver itself listed `6.8.3` as the available final release in the 6.8 line.

R1.10 makes the repair installable and transactional:

- Pins the declared GUI dependency to `PySide6==6.8.3`.
- Uses binary wheels only, avoiding accidental source builds.
- Saves the currently installed PySide6 version and restores it if the repair,
  health check, or visible Windows renderer probe fails.
- Reapplies the R1.9 deferred startup and software/Fusion rendering controls.
- Replaces zero-delay cover updates with an owned single-shot timer.
- Waits 500 ms before reopening the previous scanned book.
- Runs a real visible Windows probe for five seconds before reporting success.
- Preserves the healthy PyTorch, Kokoro, ONNX Runtime, RapidOCR, psutil, FFmpeg,
  books, projects, OCR cache, models, voices, and output.
