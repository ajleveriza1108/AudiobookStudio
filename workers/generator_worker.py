from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from core.batch import BatchProcessor
from core.project import AudiobookProject


class GeneratorWorker(QObject):
    progress = Signal(int)
    overall_progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    statistics = Signal(dict)
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
        self.export_wav = True
        self.export_mp3 = False
        self.export_m4b = False
        self.overwrite = False
        self.delete_chunks = False
        self.bitrate = "192k"

    def configure(
        self,
        export_wav=True,
        export_mp3=False,
        export_m4b=False,
        overwrite=False,
        delete_chunks=False,
        bitrate="192k",
    ):
        self.export_wav = bool(export_wav)
        self.export_mp3 = bool(export_mp3)
        self.export_m4b = bool(export_m4b)
        self.overwrite = bool(overwrite)
        self.delete_chunks = bool(delete_chunks)
        self.bitrate = str(bitrate or "192k")

    def add_job(
        self,
        source,
        output,
        voice,
        speed,
        pitch,
        engine="kokoro",
        source_sha256="",
        chapter_plan=None,
        pronunciation_rules=None,
        metadata_overrides=None,
    ):
        self.batch.add(
            source=source,
            source_sha256=source_sha256,
            output=output,
            voice=voice,
            speed=speed,
            pitch=pitch,
            engine=engine,
            chapter_plan=chapter_plan,
            pronunciation_rules=pronunciation_rules,
            metadata_overrides=metadata_overrides,
        )

    def pause(self):
        self.pause_event.clear()
        self.status.emit("Paused")

    def resume(self):
        self.pause_event.set()
        self.status.emit("Resuming")

    def cancel(self):
        self.stop_event.set()
        self.pause_event.set()

    @Slot()
    def run(self):
        try:
            total_books = self.batch.pending()
            if total_books == 0:
                self.finished.emit()
                return

            completed_books = 0
            self.log.emit(f"Queue started with {total_books} book(s).")

            while not self.batch.empty():
                if self.stop_event.is_set():
                    self.cancelled.emit()
                    return

                job = self.batch.next()
                if job is None:
                    continue

                source = Path(job.source)
                self.current_book.emit(source.name)
                self.log.emit("")
                self.log.emit("=" * 60)
                self.log.emit(f"BOOK {completed_books + 1}/{total_books}: {source.name}")
                self.log.emit("=" * 60)

                project = AudiobookProject()
                success = project.build(
                    book=source,
                    expected_source_sha256=job.source_sha256,
                    output_folder=job.output,
                    voice=job.voice,
                    speed=job.speed,
                    pitch=job.pitch,
                    engine=job.engine,
                    chapter_plan=job.chapter_plan,
                    pronunciation_rules=job.pronunciation_rules,
                    metadata_overrides=job.metadata_overrides,
                    export_wav=self.export_wav,
                    export_mp3=self.export_mp3,
                    export_m4b=self.export_m4b,
                    overwrite=self.overwrite,
                    delete_chunks=self.delete_chunks,
                    bitrate=self.bitrate,
                    progress_callback=self.progress.emit,
                    status_callback=self.status.emit,
                    log_callback=self.log.emit,
                    statistics_callback=self.statistics.emit,
                    cancel_callback=self.stop_event.is_set,
                    pause_callback=self.pause_event,
                )

                if not success:
                    self.cancelled.emit()
                    return

                completed_books += 1
                self.overall_progress.emit(int((completed_books / total_books) * 100))

            self.finished.emit()
        except Exception as error:
            self.error.emit(str(error))
