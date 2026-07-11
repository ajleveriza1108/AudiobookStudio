from PySide6.QtCore import QThread

from workers.generator_worker import GeneratorWorker
from ui.worker_callbacks import WorkerCallbacks


class ThreadManager:

    def __init__(self, window):

        self.window = window

        self.thread = None
        self.worker = None

        self.callbacks = WorkerCallbacks(window)

    def start(
        self,
        book,
        output,
        voice,
        speed,
        pitch,
        export_options
    ):

        if self.running():
            return

        # -------------------------
        # CREATE THREAD + WORKER
        # -------------------------
        self.thread = QThread()
        self.worker = GeneratorWorker()

        # -------------------------
        # CONFIGURE EXPORT OPTIONS
        # -------------------------
        self.worker.configure(
            export_mp3=export_options.get("mp3", False),
            export_m4b=export_options.get("m4b", False),
            delete_chunks=export_options.get("delete_chunks", False),
        )

        # -------------------------
        # ADD JOB (QUEUE SYSTEM)
        # -------------------------
        self.worker.add_job(
            source=book,
            output=output,
            voice=voice,
            speed=speed,
            pitch=pitch,
            engine="kokoro"
        )

        # -------------------------
        # MOVE TO THREAD
        # -------------------------
        self.worker.moveToThread(self.thread)

        # -------------------------
        # CONNECT THREAD START
        # -------------------------
        self.thread.started.connect(self.worker.run)

        # -------------------------
        # CONNECT SIGNALS
        # -------------------------
        self.connect_signals()

        # -------------------------
        # START THREAD
        # -------------------------
        self.thread.start()

    def connect_signals(self):

        w = self.worker
        c = self.callbacks

        w.progress.connect(c.progress)
        w.overall_progress.connect(c.progress)

        w.status.connect(c.status)
        w.log.connect(c.log)

        w.current_book.connect(c.current_book)

        w.finished.connect(c.finished)
        w.cancelled.connect(c.cancelled)
        w.error.connect(c.error)

        w.finished.connect(self.cleanup)
        w.cancelled.connect(self.cleanup)
        w.error.connect(self.cleanup)

    def cleanup(self):

        if self.thread is None:
            return

        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        self.thread = None
        self.worker = None

    def pause(self):

        if self.worker:
            self.worker.pause()

    def resume(self):

        if self.worker:
            self.worker.resume()

    def stop(self):

        if self.worker:
            self.worker.cancel()

    def running(self):

        if self.thread is None:
            return False

        return self.thread.isRunning()