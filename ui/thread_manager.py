from __future__ import annotations

from PySide6.QtCore import QThread, Qt

from ui.worker_callbacks import WorkerCallbacks
from workers.generator_worker import GeneratorWorker


class ThreadManager:
    def __init__(self, window):
        self.window = window
        self.thread: QThread | None = None
        self.worker: GeneratorWorker | None = None
        # WorkerCallbacks is a QObject parented to the main window.  It must
        # remain in the GUI thread for the lifetime of the window.
        self.callbacks = WorkerCallbacks(window)

    def start(self, jobs, export_options):
        if self.running() or not jobs:
            return False

        self.thread = QThread(self.window)
        self.worker = GeneratorWorker()
        self.worker.configure(
            export_wav=export_options.get("wav", True),
            export_mp3=export_options.get("mp3", False),
            export_m4b=export_options.get("m4b", False),
            overwrite=export_options.get("overwrite", False),
            delete_chunks=export_options.get("delete_chunks", False),
            bitrate=export_options.get("bitrate", "192k"),
        )

        for job in jobs:
            self.worker.add_job(**job)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self._connect_signals()
        self.thread.start()
        return True

    def _connect_signals(self):
        worker = self.worker
        thread = self.thread
        callbacks = self.callbacks
        if worker is None or thread is None:
            return

        # These connections are intentionally and explicitly queued.  OCR and
        # TTS execute in the worker thread; every widget mutation must execute
        # later on the QApplication/main thread.
        queued = Qt.ConnectionType.QueuedConnection
        worker.progress.connect(callbacks.progress, queued)
        worker.overall_progress.connect(callbacks.progress, queued)
        worker.status.connect(callbacks.status, queued)
        worker.log.connect(callbacks.log, queued)
        worker.statistics.connect(callbacks.statistics, queued)
        worker.current_book.connect(callbacks.current_book, queued)
        worker.finished.connect(callbacks.finished, queued)
        worker.cancelled.connect(callbacks.cancelled, queued)
        worker.error.connect(callbacks.error, queued)

        # Queue worker destruction before requesting thread shutdown.
        # This prevents a worker-affinity QObject from surviving until Python/Qt
        # interpreter teardown on Windows.
        worker.finished.connect(worker.deleteLater)
        worker.cancelled.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        worker.cancelled.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(self._cleanup_objects)
        thread.finished.connect(thread.deleteLater)

    def _cleanup_objects(self):
        self.worker = None
        self.thread = None

    def cleanup(self, wait_ms: int = 5000):
        if self.thread is None:
            return
        thread = self.thread
        self.stop()
        thread.quit()
        thread.wait(wait_ms)

    def pause(self):
        if self.worker:
            # Pause uses threading.Event and is intentionally immediate; the
            # worker thread is busy in run() and cannot service a queued slot.
            self.worker.pause()

    def resume(self):
        if self.worker:
            self.worker.resume()

    def stop(self):
        if self.worker:
            self.worker.cancel()

    def running(self):
        return bool(self.thread is not None and self.thread.isRunning())
