# Audiobook Studio v0.3.0 R1.12 — Final Compatibility Gate Repair

R1.11 reached and passed the real Windows post-restore paint probe. Installation
rolled back only because two older R1.4 tests monkeypatched
`ui.preview_cover.PATHS`, while the new paint-stable tile had removed that
module-level compatibility symbol. The second old test also expected a missing
source to display `No Cover`.

R1.12 keeps the R1.11 paint-safe design and restores both harmless compatibility
contracts:

- `ui.preview_cover.PATHS` exists again for older integrations and tests.
- Missing or moved book sources display `No Cover` without raising an error.
- The cover control still performs no QImage, QPixmap, QTimer, resize-event,
  show-event, custom-paint, or `setPixmap()` work.
- The R1.11 safe-start, post-restore dwell probe, and crash-loop protection remain.
- A staged preflight runs the exact previously failing tests before any installed
  source file is changed.

No AI, OCR, PySide6, FFmpeg, model, book, project, or output reinstall is needed.
