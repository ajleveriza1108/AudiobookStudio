from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ProgressManager(QObject):
    progress_changed = Signal(int)
    overall_changed = Signal(int)
    eta_changed = Signal(str)
    status_changed = Signal(str)
    chunk_changed = Signal(str)
    chapter_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.total_chunks = 0
        self.current_chunk = 0

    def begin(self):
        self.total_chunks = 0
        self.current_chunk = 0
        self.progress_changed.emit(0)
        self.overall_changed.emit(0)
        self.status_changed.emit("Starting")

    def start(self, total):
        self.total_chunks = max(0, int(total))
        self.current_chunk = 0
        self.progress_changed.emit(0)
        self.overall_changed.emit(0)

    def update(self, chunk):
        self.current_chunk = int(chunk)
        if self.total_chunks <= 0:
            return
        self.progress_changed.emit(int((self.current_chunk / self.total_chunks) * 100))

    def status(self, text):
        self.status_changed.emit(str(text))

    def eta(self, text):
        self.eta_changed.emit(str(text))

    def chapter(self, text):
        self.chapter_changed.emit(str(text))

    def chunk(self, text):
        self.chunk_changed.emit(str(text))

    def finish(self):
        self.progress_changed.emit(100)
        self.overall_changed.emit(100)
        self.status_changed.emit("Completed")
