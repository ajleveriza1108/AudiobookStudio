from __future__ import annotations

import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_worker_callback_receiver_is_a_qobject_with_typed_slots():
    source = (ROOT / "ui" / "worker_callbacks.py").read_text(encoding="utf-8")
    assert "class WorkerCallbacks(QObject)" in source
    assert "super().__init__(window)" in source
    assert "@Slot(int)" in source
    assert "@Slot(str)" in source
    assert "@Slot(dict)" in source
    assert "_require_gui_thread" in source


def test_generation_signals_are_explicitly_queued():
    source = (ROOT / "ui" / "thread_manager.py").read_text(encoding="utf-8")
    assert "Qt.ConnectionType.QueuedConnection" in source
    for signal_name in (
        "progress",
        "overall_progress",
        "status",
        "log",
        "statistics",
        "current_book",
        "finished",
        "cancelled",
        "error",
    ):
        assert f"worker.{signal_name}.connect(callbacks." in source


def test_cross_thread_progress_is_delivered_on_gui_thread():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import QObject, QEventLoop, QThread, QTimer, Qt, Signal, Slot
    from PySide6.QtWidgets import QApplication, QWidget
    from shiboken6 import isValid as is_qt_object_valid

    from ui.footer import Footer
    from ui.worker_callbacks import WorkerCallbacks

    application = QApplication.instance() or QApplication([])

    class FooterProbe(Footer):
        def __init__(self):
            self.threads = []
            super().__init__()

        def set_progress(self, value):
            self.threads.append(QThread.currentThread())
            super().set_progress(value)

    class WindowProbe(QWidget):
        def __init__(self):
            super().__init__()
            self.footer = FooterProbe()

        def set_status(self, message, state="working"):
            pass

        def log(self, message):
            pass

    class Producer(QObject):
        progress = Signal(int)
        done = Signal()

        @Slot()
        def run(self):
            for value in range(300):
                self.progress.emit(value % 101)
            self.done.emit()

    window = WindowProbe()
    callbacks = WorkerCallbacks(window)
    assert callbacks.thread() == application.thread()

    thread = QThread()
    producer = Producer()
    producer.moveToThread(thread)
    producer.progress.connect(callbacks.progress, Qt.ConnectionType.QueuedConnection)

    loop = QEventLoop()

    class Completion(QObject):
        @Slot()
        def done(self):
            QTimer.singleShot(100, loop.quit)

    completion = Completion()
    producer.done.connect(producer.deleteLater)
    producer.done.connect(thread.quit)
    thread.finished.connect(completion.done, Qt.ConnectionType.QueuedConnection)
    thread.started.connect(producer.run)
    QTimer.singleShot(5000, loop.quit)
    thread.start()
    loop.exec()
    if is_qt_object_valid(thread) and thread.isRunning():
        thread.quit()
        assert thread.wait(3000)
    application.processEvents()

    assert len(window.footer.threads) == 300
    assert all(current == application.thread() for current in window.footer.threads)

    window.close()
    window.deleteLater()
    callbacks.deleteLater()
    completion.deleteLater()
    if is_qt_object_valid(thread):
        thread.deleteLater()
    application.processEvents()
