from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Slot
from PySide6.QtWidgets import QApplication, QMessageBox


def _format_eta(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining = seconds % 60
    return f"ETA {hours:02}:{minutes:02}:{remaining:02}"


class WorkerCallbacks(QObject):
    """GUI-thread receiver for every signal emitted by the generation worker.

    This object deliberately inherits QObject and is parented to the main
    window.  Qt can therefore queue worker-thread signals to the main GUI
    thread.  A plain Python receiver is unsafe here because PySide may invoke
    it in the sender's thread, which can make QProgressBar/QLabel repaint from
    the OCR worker and terminate Windows with 0xC0000005.
    """

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def _require_gui_thread(self) -> None:
        application = QApplication.instance()
        gui_thread = application.thread() if application is not None else self.thread()
        if QThread.currentThread() != gui_thread:
            raise RuntimeError(
                "A worker callback attempted to update Qt widgets outside the GUI thread."
            )

    @Slot(int)
    def progress(self, value: int) -> None:
        self._require_gui_thread()
        self.window.footer.set_progress(value)

    @Slot(str)
    def status(self, message: str) -> None:
        self._require_gui_thread()
        self.window.footer.stage.setText(str(message))
        self.window.set_status(str(message), state="working")

    @Slot(str)
    def log(self, message: str) -> None:
        self._require_gui_thread()
        self.window.log(message)

    @Slot(dict)
    def statistics(self, stats: dict) -> None:
        self._require_gui_thread()
        self.window.workspace.statistics.update_statistics(stats)
        eta = int(stats.get("eta_seconds", 0))
        self.window.status_bar.set_eta(_format_eta(eta) if eta else "ETA --:--")
        self.window.footer.set_center(
            f"Section {int(stats.get('generated', 0))} of {int(stats.get('total', 0))}"
        )
        self.window.refresh_engine_status()

    @Slot(str)
    def current_book(self, book: str) -> None:
        self._require_gui_thread()
        self.window.set_status(f"Processing: {book}", state="working")
        self.window.footer.set_left(str(book))

    @Slot()
    def finished(self) -> None:
        self._require_gui_thread()
        self.window.controller.generation.finished()
        self.window.log("Generation completed successfully.")

    @Slot()
    def cancelled(self) -> None:
        self._require_gui_thread()
        self.window.controller.generation.cancelled()
        self.window.log("Generation stopped. Completed sections were kept for resume.")

    @Slot(str)
    def error(self, message: str) -> None:
        self._require_gui_thread()
        self.window.controller.generation.failed()
        self.window.log(f"Generation error: {message}")
        QMessageBox.critical(
            self.window,
            "Audiobook could not be completed",
            "Audiobook Studio stopped safely. Completed narration sections were kept, "
            "so you can correct the problem and resume.\n\n"
            f"Reason: {message}",
        )
