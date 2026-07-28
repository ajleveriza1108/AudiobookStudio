# Audiobook Studio v0.3.0 R1.13

## Root cause repaired

The Windows crash was not a damaged Qt installation or an image-cover repaint defect. The
native crash stack showed that OCR progress was calling `Footer.set_progress()` from the
generation worker thread. `WorkerCallbacks` had been a plain Python object, so PySide could
invoke its methods in the signal sender's thread. Mutating `QProgressBar` and `QLabel` from
that thread caused recursive repaint warnings and the Windows access violation `0xC0000005`.

R1.13 makes `WorkerCallbacks` a GUI-owned `QObject`, declares typed Qt slots, and connects
every generation signal with `Qt.QueuedConnection`. Progress, status, logging, statistics,
completion, cancellation, and error UI work now execute only on the QApplication thread.

A new visible Windows stress probe sends thousands of progress updates from a real QThread
while the footer repaints. Verification cannot pass unless all updates are received on the
main GUI thread.

The existing `.venv`, PySide6 6.8.3, PyTorch, Kokoro, RapidOCR, ONNX Runtime, FFmpeg, books,
projects, OCR cache, voices, output, and local settings are preserved.
