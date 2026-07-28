# Audiobook Studio v0.3.0 R1.11 — Post-Restore Paint and Crash-Loop Repair

R1.10 proved that the isolated Python runtime, PyTorch, ONNX Runtime,
RapidOCR, Kokoro, PySide6 6.8.3, FFmpeg, and the test suite were healthy. The
real application still crashed after verification with:

```
QWidget::repaint: Recursive repaint detected
QBackingStore::endPaint() called with active painter
0xC0000005
```

The R1.10 probe could falsely pass because its quit timer began before the last
scanned PDF was restored. A slow restore blocked the GUI thread; when it
returned, the overdue quit event could close the app before the delayed cover
pixmap timer executed.

R1.11 permanently removes that path:

- The overview uses a paint-stable text document tile. It performs no QImage,
  QPixmap, QTimer, resize-event, show-event, or custom paint work.
- Runtime status changes no longer replace a widget stylesheet.
- The real Windows probe begins its eight-second visible dwell only after the
  previous book has completely restored.
- The probe must write a post-restore completion marker or verification fails.
- A clean-shutdown flag prevents crash loops. After an unclean exit, recent
  books remain in Library but the last book is not automatically opened.
- Normal clean shutdowns continue restoring the last book on the next launch.

Cover artwork is intentionally disabled in this stability release. PDF/EPUB
text extraction, offline OCR, chapter planning, Kokoro narration, audio export,
and project recovery remain enabled.
