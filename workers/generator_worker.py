from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from core.project import AudiobookProject
from core.batch import BatchProcessor


class GeneratorWorker(QObject):

    progress = Signal(int)
    overall_progress = Signal(int)

    status = Signal(str)
    log = Signal(str)

    finished = Signal()
    cancelled = Signal()
    error = Signal(str)

    current_book = Signal(str)

    def __init__(self):

        super().__init__()

        self.batch = BatchProcessor()

        self.stop_event = Event()
        self.pause_event = Event()
        self.pause_event.set()

        self.export_mp3 = False
        self.export_m4b = False
        self.delete_chunks = False

    def configure(self, export_mp3=False, export_m4b=False, delete_chunks=False):

        self.export_mp3 = export_mp3
        self.export_m4b = export_m4b
        self.delete_chunks = delete_chunks

    def add_job(self, source, output, voice, speed, pitch, engine="kokoro"):

        self.batch.add(
            source=source,
            output=output,
            voice=voice,
            speed=speed,
            pitch=pitch,
            engine=engine
        )

    def pause(self):

        self.pause_event.clear()
        self.status.emit("Paused")

    def resume(self):

        self.pause_event.set()
        self.status.emit("Resumed")

    def cancel(self):

        self.stop_event.set()
        self.pause_event.set()

    def _get_total_books(self):

        try:
            return len(self.batch)
        except Exception:
            pass

        if hasattr(self.batch, "jobs"):
            return len(self.batch.jobs)

        if hasattr(self.batch, "queue"):
            return len(self.batch.queue)

        if hasattr(self.batch, "_queue"):
            return len(self.batch._queue)

        return 0

    @Slot()
    def run(self):

        try:

            self.log.emit("WORKER STARTED")

            total_books = self._get_total_books()

            self.log.emit(f"BATCH SIZE: {total_books}")

            if total_books == 0:

                self.log.emit("NO JOBS FOUND - EXITING WORKER")

                self.finished.emit()

                return

            finished_books = 0

            while not self.batch.empty():

                if self.stop_event.is_set():

                    self.log.emit("CANCELLED BY USER")

                    self.cancelled.emit()

                    return

                job = self.batch.next()

                if job is None:

                    self.log.emit("JOB IS NONE - SKIPPING")

                    continue

                source = Path(job.source)

                self.current_book.emit(source.name)

                self.log.emit("")
                self.log.emit("=" * 60)
                self.log.emit(f"BOOK {finished_books + 1}/{total_books}")
                self.log.emit(source.name)
                self.log.emit("=" * 60)

                try:

                    project = AudiobookProject()

                    success = project.build(

                        book=source,
                        output_folder=job.output,
                        voice=job.voice,
                        speed=job.speed,
                        pitch=job.pitch,

                        export_mp3=self.export_mp3,
                        export_m4b=self.export_m4b,
                        delete_chunks=self.delete_chunks,

                        progress_callback=self.progress.emit,
                        status_callback=self.status.emit,
                        log_callback=self.log.emit,
                        cancel_callback=self.stop_event.is_set,
                        pause_callback=self.pause_event
                    )

                    if not success:

                        self.log.emit("PROJECT FAILED - STOPPING")

                        self.error.emit("Generation failed")

                        return

                except Exception as e:

                    self.log.emit(f"ERROR IN PROJECT: {e}")

                    self.error.emit(str(e))

                    return

                finished_books += 1

                percent = int((finished_books / total_books) * 100)

                self.overall_progress.emit(percent)

                self.log.emit("BOOK COMPLETED")

            self.log.emit("ALL BOOKS DONE")

            self.finished.emit()

        except Exception as e:

            self.log.emit(f"WORKER CRASH: {e}")

            self.error.emit(str(e))