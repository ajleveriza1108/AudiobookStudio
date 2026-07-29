from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from core.ffmpeg import FFmpeg
from core.ocr import OCRService
from core.ocr_corrections import content_sha256
from engines.manager import EngineManager


class GenerationController:
    def __init__(self, window):
        self.window = window

    def _common_settings(self) -> dict:
        settings = self.window.central.settings
        options = settings.export_options()
        return {
            "output": str(self.window.output_folder),
            "voice": settings.current_voice(),
            "speed": settings.current_speed(),
            "pitch": settings.current_pitch(),
            "engine": settings.current_engine(),
            "export_options": options,
            "pronunciation_rules": settings.pronunciation_rules(),
        }

    def _validate(self, books: list[str]) -> dict | None:
        if not books:
            QMessageBox.warning(
                self.window,
                "No Book Selected",
                "Import a PDF or EPUB before starting narration.",
            )
            return None

        missing = [book for book in books if not Path(book).is_file()]
        if missing:
            QMessageBox.warning(
                self.window,
                "Book File Missing",
                "One or more selected books can no longer be found.",
            )
            return None

        values = self._common_settings()
        output = Path(values["output"])
        try:
            output.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(
                self.window,
                "Output Folder Unavailable",
                f"Audiobook Studio could not use the selected output folder.\n\n{error}",
            )
            return None

        engine_id = str(values.get("engine", "kokoro"))
        engine_record = next(
            (item for item in EngineManager().available() if str(item.get("name")) == engine_id),
            None,
        )
        if not engine_record or engine_record.get("status") != "Available":
            missing = ", ".join((engine_record or {}).get("missing_dependencies", []) or [])
            detail = f" Missing: {missing}." if missing else ""
            QMessageBox.warning(
                self.window,
                "Narration Engine Unavailable",
                f"The selected engine is not ready on this computer.{detail}",
            )
            return None

        options = values["export_options"]
        if not any(options.get(name, False) for name in ("wav", "mp3", "m4b")):
            QMessageBox.warning(
                self.window,
                "Choose an Audio Format",
                "Select WAV, MP3, or M4B before starting.",
            )
            return None

        if (options.get("mp3") or options.get("m4b")) and not FFmpeg.exists():
            QMessageBox.warning(
                self.window,
                "FFmpeg Required",
                "MP3 and M4B export need FFmpeg. Install FFmpeg or select WAV only.",
            )
            return None

        current = self.window.controller.books.book
        if current and any(Path(book).resolve() == Path(current).resolve() for book in books):
            preview = self.window.central.preview
            if preview.is_ocr_required():
                availability = OCRService.availability()
                if not availability.available:
                    QMessageBox.warning(
                        self.window,
                        "Offline OCR Required",
                        "This PDF contains scanned page images and has no embedded text. "
                        "Run install_dependencies.ps1 to install RapidOCR and ONNX Runtime, "
                        "then reopen Audiobook Studio.",
                    )
                    return None

                reply = QMessageBox.question(
                    self.window,
                    "Read Scanned PDF with Offline OCR",
                    "This PDF is made from scanned page images. Audiobook Studio will now "
                    "read every page with offline OCR, cache the recognized text, and then "
                    "continue into narration. The original PDF will not be changed.\n\n"
                    "OCR can take several minutes depending on the number and quality of pages. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return None
            elif preview.included_chapter_count() <= 0:
                QMessageBox.warning(
                    self.window,
                    "No Sections Included",
                    "Open the Chapters tab and include at least one section.",
                )
                return None

            warnings = preview.preparation_warning_count()
            if warnings and not preview.is_ocr_required():
                reply = QMessageBox.question(
                    self.window,
                    "Book Preparation Review",
                    f"The preparation report contains {warnings} warning(s). "
                    "Continue with the current cleaned text and chapter plan?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return None

        return values

    def _start(self, books: list[str], clear_queue: bool = False):
        values = self._validate(books)
        if values is None:
            return

        current = self.window.controller.books.book
        current_resolved = Path(current).resolve() if current else None
        metadata = {
            key: value
            for key, value in self.window.central.settings.metadata_overrides().items()
            if value not in (None, "")
        }

        jobs = []
        for book in books:
            source = Path(book).resolve()
            source_sha256 = content_sha256(source)
            is_current = bool(current_resolved and source == current_resolved)
            self.window.log(f"Queued exact selected source: {source}")
            self.window.log(f"Selected source SHA-256: {source_sha256}")
            jobs.append(
                {
                    "source": str(source),
                    "source_sha256": source_sha256,
                    "output": values["output"],
                    "voice": values["voice"],
                    "speed": values["speed"],
                    "pitch": values["pitch"],
                    "engine": values["engine"],
                    # A scanned PDF has no trustworthy chapter plan until OCR has
                    # read the pages. Let the generation worker detect headings from
                    # the recognized text; it will create one Full Book section when
                    # no headings exist.
                    "chapter_plan": (
                        []
                        if is_current and self.window.central.preview.is_ocr_required()
                        else self.window.central.preview.chapter_plan() if is_current else []
                    ),
                    "pronunciation_rules": values["pronunciation_rules"],
                    "metadata_overrides": metadata if is_current else {},
                }
            )

        self.window.controller.progress.begin()
        self.window.workspace.statistics.reset()
        self.window.footer.set_progress(0)
        self.window.footer.stage.setText("Starting")
        self.window.footer.set_running(True)
        self.window.central.settings.set_generation_running(True)
        self.window.header.set_status("Working", state="working")
        self.window.status_bar.set_message("Preparing audiobook production")
        self.window.footer.set_right(f"Loading {values['engine'].title()} on first narration section…")
        self.window.status_bar.set_backend(f"Loading {values['engine'].title()}…")

        started = self.window.controller.threads.start(
            jobs=jobs,
            export_options=values["export_options"],
        )
        if not started:
            self.window.central.settings.set_generation_running(False)
            self.window.footer.set_running(False)
            self.window.header.set_status("Ready")
            return

        if clear_queue:
            self.window.workspace.queue.clear_after_start()

        self.window.save_generation_settings()

    def generate(self):
        book = self.window.controller.books.book
        self._start([str(book)] if book else [])

    def generate_queue(self):
        self._start(self.window.workspace.queue.queued_sources(), clear_queue=True)

    def pause(self):
        if not self.window.controller.threads.running():
            return
        self.window.controller.threads.pause()
        self.window.footer.set_paused(True)
        self.window.header.set_status("Paused", state="paused")
        self.window.status_bar.set_message("Generation paused")

    def resume(self):
        if not self.window.controller.threads.running():
            return
        self.window.controller.threads.resume()
        self.window.footer.set_paused(False)
        self.window.header.set_status("Working", state="working")
        self.window.status_bar.set_message("Generation resumed")

    def stop(self):
        if not self.window.controller.threads.running():
            return
        reply = QMessageBox.question(
            self.window,
            "Stop Generation",
            "Stop after the current narration operation? Completed sections will be kept for resume.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.window.controller.threads.stop()
            self.window.footer.stage.setText("Stopping safely")
            self.window.status_bar.set_message("Stopping safely")

    def _reset_controls(self):
        self.window.footer.pause.setEnabled(False)
        self.window.footer.resume.setEnabled(False)
        self.window.footer.stop.setEnabled(False)
        self.window.central.settings.set_generation_running(False)
        self.window.status_bar.set_eta("ETA --:--")

    def finished(self):
        self._reset_controls()
        self.window.footer.set_progress(100)
        self.window.footer.stage.setText("Finished")
        self.window.header.set_status("Finished", state="ready")
        self.window.status_bar.set_message("Audiobook completed")
        self.window.refresh_engine_status()

    def cancelled(self):
        self._reset_controls()
        self.window.footer.stage.setText("Stopped")
        self.window.header.set_status("Ready", state="ready")
        self.window.status_bar.set_message("Generation stopped; resume data was kept")
        self.window.refresh_engine_status()

    def failed(self):
        self._reset_controls()
        self.window.footer.stage.setText("Needs attention")
        self.window.header.set_status("Needs attention", state="error")
        self.window.status_bar.set_message("Generation stopped safely")
        self.window.refresh_engine_status()
