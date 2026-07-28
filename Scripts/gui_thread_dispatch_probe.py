from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from shiboken6 import isValid as is_qt_object_valid

from ui.footer import Footer
from ui.thread_manager import ThreadManager


class ProbeFooter(Footer):
    def __init__(self, application: QApplication):
        self.application = application
        self.thread_violations = 0
        self.update_count = 0
        super().__init__()

    def set_progress(self, value: int):
        if QThread.currentThread() != self.application.thread():
            self.thread_violations += 1
        self.update_count += 1
        super().set_progress(value)


class ProbeWindow(QWidget):
    def __init__(self, application: QApplication):
        super().__init__()
        self.footer = ProbeFooter(application)
        self.status_messages: list[str] = []
        layout = QVBoxLayout(self)
        layout.addWidget(self.footer)
        self.resize(900, 140)
        self.setWindowTitle("Audiobook Studio GUI Thread Dispatch Probe")

    def set_status(self, message: str, state: str = "working") -> None:
        self.status_messages.append(f"{state}:{message}")

    def log(self, message: str) -> None:
        pass


class Producer(QObject):
    progress = Signal(int)
    overall_progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    statistics = Signal(dict)
    current_book = Signal(str)
    finished = Signal()
    cancelled = Signal()
    error = Signal(str)
    probe_done = Signal()

    def __init__(self, updates: int):
        super().__init__()
        self.updates = max(200, int(updates))

    @Slot()
    def run(self) -> None:
        for index in range(self.updates):
            self.progress.emit(index % 101)
            if index % 40 == 0:
                self.status.emit(f"Worker update {index}")
            time.sleep(0.0005)
        self.probe_done.emit()


class CompletionReceiver(QObject):
    def __init__(self, application: QApplication, result: dict[str, bool]):
        super().__init__()
        self.application = application
        self.result = result

    @Slot()
    def thread_finished(self) -> None:
        self.result["done"] = True
        QTimer.singleShot(800, self.application.quit)


def qt_object_is_alive(obj: object | None) -> bool:
    """Return False when the Python wrapper outlives its deleted C++ object."""
    if obj is None:
        return False
    try:
        return bool(is_qt_object_valid(obj))
    except (RuntimeError, TypeError):
        return False


def request_thread_stop(thread: QThread | None, wait_ms: int = 0) -> None:
    """Stop a QThread only while its underlying Qt object still exists."""
    if not qt_object_is_alive(thread):
        return
    try:
        if thread.isRunning():
            thread.requestInterruption()
            thread.quit()
            if wait_ms > 0:
                thread.wait(wait_ms)
    except RuntimeError:
        # ThreadManager may have received finished and deleted the QThread
        # between the validity check and this call. That is normal cleanup.
        return


def delete_later_if_alive(obj: object | None) -> None:
    if not qt_object_is_alive(obj):
        return
    try:
        obj.deleteLater()
    except RuntimeError:
        return


def finish(code: int) -> int:
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == "nt":
        # Functional success/failure has already been determined. Avoid Qt
        # interpreter-teardown faults in this disposable verification process.
        os._exit(int(code))
    return int(code)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-thread Qt widget dispatch probe")
    parser.add_argument("--updates", type=int, default=4000)
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--visible", action="store_true")
    args = parser.parse_args()

    application = QApplication.instance() or QApplication([])
    window = ProbeWindow(application)
    thread = QThread()
    producer = Producer(args.updates)
    producer.moveToThread(thread)

    manager = ThreadManager(window)
    manager.thread = thread
    manager.worker = producer
    if manager.callbacks.thread() != application.thread():
        print("WorkerCallbacks was not created in the QApplication thread.", file=sys.stderr)
        return finish(2)
    manager._connect_signals()

    queued = Qt.ConnectionType.QueuedConnection
    result = {"done": False, "timed_out": False}
    completion = CompletionReceiver(application, result)

    producer.probe_done.connect(producer.deleteLater)
    producer.probe_done.connect(thread.quit)
    thread.finished.connect(completion.thread_finished, queued)
    thread.started.connect(producer.run)

    def timeout() -> None:
        result["timed_out"] = True
        request_thread_stop(thread)
        application.quit()

    QTimer.singleShot(max(5000, int(args.timeout_ms)), timeout)
    if args.visible and os.name == "nt":
        window.show()
    thread.start()
    application.exec()

    # ThreadManager connects thread.finished to thread.deleteLater. By the time
    # QApplication.exec() returns, the QThread C++ object may already be gone.
    # Never call quit(), wait(), or deleteLater() on an invalid wrapper.
    request_thread_stop(thread, wait_ms=5000)

    code = 0
    if result["timed_out"] or not result["done"]:
        print("GUI thread dispatch probe timed out.", file=sys.stderr)
        code = 3
    elif window.footer.thread_violations:
        print(
            f"Detected {window.footer.thread_violations} widget updates outside the GUI thread.",
            file=sys.stderr,
        )
        code = 4
    elif window.footer.update_count < args.updates:
        print(
            f"Only {window.footer.update_count} of {args.updates} queued progress updates were applied.",
            file=sys.stderr,
        )
        code = 5
    else:
        print(
            "GUI worker-to-main-thread dispatch probe: PASS "
            f"({window.footer.update_count} progress updates)"
        )

    if qt_object_is_alive(window):
        window.close()
    delete_later_if_alive(window)
    delete_later_if_alive(completion)
    delete_later_if_alive(thread)
    application.processEvents()
    return finish(code)


if __name__ == "__main__":
    raise SystemExit(main())
