from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from core.audio_quality import AudioQualityAnalyzer
from core.book_preparation import analyze_book_text, format_preparation_report
from core.chapter_timing import build_chapter_timings
from core.chapters import apply_chapter_plan
from core.cover import CoverExtractor
from core.exporter import Exporter
from core.generator import AudiobookGenerator
from core.generation_integrity import (
    GenerationIntegrityError,
    promote_candidate,
    require_chunk_integrity,
    require_merged_audio_integrity,
    require_pre_generation_integrity,
    save_report as save_integrity_report,
)
from core.library import Library
from core.logger import Logger
from core.merger import AudioMerger
from core.narration_plan import build_narration_plan
from core.parser import extract_book_text, parse_book
from core.ocr_corrections import content_sha256
from core.pronunciation import PronunciationDictionary
from core.replacer import Replacer
from core.resume import ResumeManager
from core.statistics import Statistics


class AudiobookProject:
    def __init__(self):
        self.merger = AudioMerger()
        self.library = Library()
        self.logger = Logger()
        self.dictionary = PronunciationDictionary()
        self.replacer = Replacer()
        self.exporter = Exporter()
        self.cover_extractor = CoverExtractor()

    @staticmethod
    def _emit(callback, value):
        if callback:
            callback(value)

    @staticmethod
    def _atomic_text(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, path)

    @staticmethod
    def _wait_if_paused(pause_callback, cancel_callback=None) -> bool:
        if pause_callback is None:
            return True
        while not pause_callback.is_set():
            if cancel_callback and cancel_callback():
                return False
            pause_callback.wait(0.2)
        return not (cancel_callback and cancel_callback())

    @staticmethod
    def _apply_title(section: dict[str, Any]) -> str:
        text = str(section.get("text", "") or "").strip()
        title = str(section.get("title", "") or "").strip()
        source_title = str(section.get("source_title", "") or "").strip()
        if title and source_title and title != source_title and text.startswith(source_title):
            return title + text[len(source_title):]
        return text

    def build(
        self,
        book,
        output_folder,
        voice,
        speed,
        pitch,
        engine="kokoro",
        progress_callback=None,
        status_callback=None,
        log_callback=None,
        statistics_callback=None,
        cancel_callback=None,
        pause_callback=None,
        export_wav=True,
        export_mp3=False,
        export_m4b=False,
        delete_chunks=False,
        overwrite=False,
        replace_rules=None,
        bitrate="192k",
        chapter_plan=None,
        pronunciation_rules=None,
        metadata_overrides=None,
        expected_source_sha256="",
    ):
        book = Path(book).expanduser().resolve()
        if not book.is_file():
            raise FileNotFoundError(book)

        selected_source_sha256 = content_sha256(book).casefold()
        expected_source_sha256 = str(expected_source_sha256 or "").casefold()
        if expected_source_sha256 and selected_source_sha256 != expected_source_sha256:
            raise RuntimeError(
                "The selected source file changed after it was queued. "
                "Select the PDF again before generating."
            )

        output_root = Path(output_folder).expanduser().resolve()
        project_name = (
            f"{book.stem}__{selected_source_sha256[:12]}"
            if expected_source_sha256
            else book.stem
        )
        project = output_root / project_name
        project.mkdir(parents=True, exist_ok=True)

        initial_source_record = {
            "schema": 2,
            "status": "selected",
            "selected_source": str(book),
            "source_name": book.name,
            "source_sha256": selected_source_sha256,
            "source_size": int(book.stat().st_size),
            "project_folder": str(project),
            "narration_source": "selected-file-extraction",
            "hardcoded_profile_allowed": False,
        }
        self.exporter._atomic_json(project / "Selected Source.json", initial_source_record)

        self.library.add(book)
        self._emit(progress_callback, 0)
        self._emit(status_callback, "Reading selected book")
        self._emit(log_callback, f"Selected PDF: {book}")
        self._emit(log_callback, f"Selected PDF SHA-256: {selected_source_sha256}")
        self._emit(log_callback, f"Source-specific project: {project}")

        if cancel_callback and cancel_callback():
            return False

        text_diagnostics: dict[str, Any] = {}

        def ocr_progress(page_number: int, total_pages: int, stage: str) -> None:
            total_pages = max(1, int(total_pages))
            page_number = max(0, min(total_pages, int(page_number)))
            self._emit(
                status_callback,
                f"Reading scanned page {page_number}/{total_pages}",
            )
            self._emit(progress_callback, min(14, int((page_number / total_pages) * 14)))

        raw_text = extract_book_text(
            book,
            ocr_if_needed=True,
            progress_callback=ocr_progress,
            cancel_callback=cancel_callback,
            log_callback=log_callback,
            diagnostics=text_diagnostics,
        )
        self._emit(progress_callback, 15)

        completed_source_sha256 = content_sha256(book).casefold()
        if completed_source_sha256 != selected_source_sha256:
            raise RuntimeError(
                "The selected source file changed while it was being read. "
                "Generation was stopped before narration."
            )

        if text_diagnostics.get("ocr_used"):
            cache_note = " from cache" if text_diagnostics.get("ocr_cache_hit") else ""
            self._emit(
                log_callback,
                f"Offline OCR completed{cache_note} using "
                f"{text_diagnostics.get('ocr_backend') or 'the local OCR engine'}.",
            )
            structured = int(text_diagnostics.get("structured_pages") or 0)
            timelines = int(text_diagnostics.get("timeline_pages") or 0)
            columns = int(text_diagnostics.get("multi_column_pages") or 0)
            if structured:
                self._emit(
                    log_callback,
                    "Layout-aware OCR ordered "
                    f"{structured} structured page(s) "
                    f"({timelines} timeline, {columns} multi-column).",
                )
            advanced_pages = int(text_diagnostics.get("advanced_pages") or 0)
            fallback_pages = int(text_diagnostics.get("fallback_pages") or 0)
            if advanced_pages:
                self._emit(
                    log_callback,
                    f"Unlimited-OCR supplied semantic reading order for {advanced_pages} page(s).",
                )
            if fallback_pages:
                self._emit(
                    log_callback,
                    f"RapidOCR fallback protected {fallback_pages} page(s) rejected by Advanced OCR.",
                )
            correction_profile = str(text_diagnostics.get("correction_profile") or "").strip()
            if correction_profile:
                self._emit(
                    log_callback,
                    f"Verified narration correction profile applied: {correction_profile}.",
                )

        if not self._wait_if_paused(pause_callback, cancel_callback):
            return False

        self._emit(status_callback, "Preparing narration text")
        from core.cleaner import clean_text

        cleaned_text = clean_text(raw_text)
        if not cleaned_text.strip():
            raise RuntimeError("No readable narration text remained after preparation.")

        metadata = parse_book(book)
        metadata.update(dict(metadata_overrides or {}))
        metadata["source"] = str(book)
        metadata["source_sha256"] = selected_source_sha256
        metadata["source_project_key"] = selected_source_sha256[:12]
        book_language = str(metadata.get("language") or "all")

        selected_source_record = dict(initial_source_record)
        selected_source_record.update(
            {
                "status": "text-extracted",
                "source_pages": int(metadata.get("pages") or 0),
                "text_source": str(text_diagnostics.get("source_mode") or "embedded"),
                "ocr_used": bool(text_diagnostics.get("ocr_used")),
                "ocr_backend": str(text_diagnostics.get("ocr_backend") or ""),
                "ocr_cache_hit": bool(text_diagnostics.get("ocr_cache_hit")),
                "ocr_correction_profile": str(
                    text_diagnostics.get("correction_profile") or ""
                ),
            }
        )
        self.exporter._atomic_json(project / "Selected Source.json", selected_source_record)

        preparation_report = analyze_book_text(
            raw_text, cleaned_text, book, diagnostics=text_diagnostics
        )
        self.exporter.export_preparation_report(project, preparation_report)
        self._atomic_text(
            project / "Book Preparation Report.txt",
            format_preparation_report(preparation_report),
        )
        cache_folder = Path(str(text_diagnostics.get("ocr_cache_folder") or ""))
        layout_report = cache_folder / "layout_report.json" if str(cache_folder) not in {"", "."} else None
        if layout_report is not None and layout_report.is_file():
            shutil.copy2(layout_report, project / "OCR Reading Order Report.json")
        for issue in preparation_report.get("issues", []):
            self._emit(
                log_callback,
                f"Preparation {str(issue.get('severity', 'notice')).upper()}: "
                f"{issue.get('title', 'Review item')}",
            )

        selected_sections = apply_chapter_plan(cleaned_text, chapter_plan)
        if not selected_sections:
            raise RuntimeError("All detected chapters were excluded. Include at least one chapter.")

        processed_sections: list[dict[str, Any]] = []
        for section in selected_sections:
            section = dict(section)
            section_text = self._apply_title(section)
            section_text = self.dictionary.replace(
                section_text,
                extra_rules=pronunciation_rules,
                language=book_language,
            )
            if replace_rules:
                self.replacer.set_rules(replace_rules)
                section_text = self.replacer.process(section_text)
            section["text"] = section_text.strip()
            if section["text"]:
                processed_sections.append(section)

        chunks, chapters, narration_text = build_narration_plan(processed_sections)

        integrity_report = require_pre_generation_integrity(
            project,
            source=book,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            narration_text=narration_text,
            chunks=chunks,
            chapters=chapters,
            chapter_plan=chapter_plan,
            metadata=metadata,
            diagnostics=text_diagnostics,
        )
        self._emit(
            log_callback,
            "Generation integrity preflight passed: "
            f"{integrity_report.get('extracted_pages', 0)} page(s), "
            f"{integrity_report.get('narration_words', 0)} narration word(s).",
        )

        narration_quality_report = {
            "schema": 1,
            "profile": "known-good-audio-r1.17.3",
            "engine_settings_locked": {
                "engine": str(engine),
                "voice": str(voice),
                "speed": float(speed),
                "pitch": float(pitch),
            },
            "chapter_preparation": [
                {
                    "title": str(section.get("title", "")),
                    **dict(section.get("narration_preparation") or {}),
                }
                for section in processed_sections
            ],
            "rules": {
                "remove_repeated_margins": True,
                "remove_decorative_lines": True,
                "protect_timeline_items": True,
                "protect_lists_and_label_value_rows": True,
                "complete_sentence_boundaries": True,
                "audio_engine_defaults_changed": False,
            },
        }
        self.exporter._atomic_json(
            project / "narration_quality_report.json",
            narration_quality_report,
        )
        total = len(chunks)
        if total == 0:
            raise RuntimeError("No narration sections were created.")

        self._emit(log_callback, f"Included {len(chapters)} chapter(s).")
        self._emit(log_callback, f"Prepared {total} narration section(s).")
        self._emit(progress_callback, 20)

        metadata.update(
            {
                "source": str(book),
                "engine": str(engine),
                "voice": str(voice),
                "narrator": str((metadata_overrides or {}).get("narrator") or voice),
                "speed": float(speed),
                "pitch": float(pitch),
                "chunks": total,
                "chapters": len(chapters),
                "schema": 5,
                "narration_quality_profile": "known-good-audio-r1.17.3",
                "text_source": str(text_diagnostics.get("source_mode") or "embedded"),
                "ocr_used": bool(text_diagnostics.get("ocr_used")),
                "ocr_backend": str(text_diagnostics.get("ocr_backend") or ""),
                "ocr_layout_schema": int(text_diagnostics.get("layout_schema") or 0),
                "structured_ocr_pages": int(text_diagnostics.get("structured_pages") or 0),
                "timeline_pages": int(text_diagnostics.get("timeline_pages") or 0),
                "multi_column_pages": int(text_diagnostics.get("multi_column_pages") or 0),
                "low_confidence_ocr_pages": int(text_diagnostics.get("low_confidence_pages") or 0),
                "ocr_correction_profile": str(text_diagnostics.get("correction_profile") or ""),
                "advanced_ocr_pages": int(text_diagnostics.get("advanced_pages") or 0),
                "advanced_ocr_fallback_pages": int(text_diagnostics.get("fallback_pages") or 0),
                "generation_integrity_schema": int(integrity_report.get("schema") or 1),
                "source_pages_verified": int(integrity_report.get("source_pages") or 0),
                "extracted_pages_verified": int(integrity_report.get("extracted_pages") or 0),
                "narration_words_verified": int(integrity_report.get("narration_words") or 0),
            }
        )

        cover_file = self.cover_extractor.extract(book, project)
        if cover_file:
            metadata["cover"] = str(cover_file)

        self.exporter.save_project(project, metadata)
        self.exporter.export_metadata(project, metadata)
        self.exporter.export_chapters(project, chapters)
        self.exporter.export_narration_plan(project, chapters)
        self._atomic_text(project / "narration_text.txt", narration_text)

        text_hash = hashlib.sha256(narration_text.encode("utf-8")).hexdigest()
        resume = ResumeManager(project)
        generator = AudiobookGenerator(engine=engine)

        def generation_progress(value: int) -> None:
            self._emit(progress_callback, 20 + int(value * 0.65))

        self._emit(status_callback, "Starting narration")
        success = generator.generate(
            title=book.stem,
            chunks=chunks,
            output_folder=project,
            voice=voice,
            speed=speed,
            pitch=pitch,
            engine=engine,
            overwrite=overwrite,
            progress_callback=generation_progress,
            log_callback=log_callback,
            cancel_callback=cancel_callback,
            pause_callback=pause_callback,
            statistics_callback=statistics_callback,
            status_callback=status_callback,
            resume_manager=resume,
            source_file=book,
            text_hash=text_hash,
        )

        if not success:
            return False

        integrity_report = require_chunk_integrity(
            project,
            expected_total=total,
            base_report=integrity_report,
        )
        self._emit(
            log_callback,
            f"Verified all {total} narration section file(s) before assembly.",
        )

        if cancel_callback and cancel_callback():
            return False
        if not self._wait_if_paused(pause_callback, cancel_callback):
            return False

        self._emit(status_callback, "Combining narration sections")

        def merge_progress(index: int, merge_total: int) -> None:
            value = 85 + int((index / max(1, merge_total)) * 11)
            self._emit(progress_callback, min(value, 96))

        final_wav = project / "audiobook.wav"
        candidate_wav = project / "audiobook.candidate.wav"
        candidate_wav.unlink(missing_ok=True)

        try:
            merged = self.merger.merge(
                input_folder=project,
                output_file=candidate_wav,
                # The candidate is assembled first. Existing approved audio is
                # untouched until completeness and frame-count checks pass.
                export_wav=True,
                export_mp3=False,
                export_m4b=False,
                bitrate=bitrate,
                delete_chunks=False,
                progress_callback=merge_progress,
                cancel_callback=cancel_callback,
                pause_callback=pause_callback,
                title=str(metadata.get("title") or book.stem),
                expected_total=total,
                metadata=metadata,
                chapter_map=chapters,
                cover_file=cover_file,
            )

            if not merged:
                candidate_wav.unlink(missing_ok=True)
                return False

            integrity_report = require_merged_audio_integrity(
                project,
                candidate=candidate_wav,
                chunk_folder=project,
                expected_total=total,
                narration_words=int(integrity_report.get("narration_words") or 0),
                speed=float(speed),
                base_report=integrity_report,
            )

            previous_wav = promote_candidate(candidate_wav, final_wav)
            if previous_wav is not None:
                integrity_report["previous_audio_backup"] = str(previous_wav)
                self._emit(
                    log_callback,
                    f"Previous audiobook preserved: {previous_wav}",
                )
            integrity_report["stage"] = "completed"
            integrity_report["status"] = "passed"
            save_integrity_report(project, integrity_report)

            # Compressed exports are created only after the verified WAV has been
            # promoted. A failed MP3/M4B export therefore cannot destroy the WAV.
            if export_mp3:
                self.merger._export_mp3(
                    final_wav,
                    final_wav.with_suffix(".mp3"),
                    bitrate,
                    metadata,
                    Path(cover_file) if cover_file else None,
                )
            if export_m4b:
                chapter_timings = build_chapter_timings(project, chapters)
                self.merger._export_m4b(
                    final_wav,
                    final_wav.with_suffix(".m4b"),
                    bitrate,
                    metadata,
                    chapter_timings,
                    Path(cover_file) if cover_file else None,
                )

            self._emit(progress_callback, 97)
            self._emit(status_callback, "Checking final audio")
            quality = AudioQualityAnalyzer.analyze(final_wav)
            AudioQualityAnalyzer.save(quality, project)
            for warning in quality.get("warnings", []):
                self._emit(log_callback, f"Audio review: {warning}")

            if delete_chunks:
                for name in integrity_report.get("chunk_validation", {}).get("files", []):
                    (project / str(name)).unlink(missing_ok=True)

            if not export_wav and (export_mp3 or export_m4b):
                final_wav.unlink(missing_ok=True)
        except GenerationIntegrityError:
            candidate_wav.unlink(missing_ok=True)
            raise
        except Exception:
            candidate_wav.unlink(missing_ok=True)
            raise

        stats = Statistics.audiobook(project)
        self.library.update_progress(book, 100)
        resume.finish()
        self.logger.success(f"Finished: {book.name}")

        self._emit(progress_callback, 100)
        self._emit(status_callback, "Finished")
        self._emit(log_callback, "")
        self._emit(log_callback, "=" * 70)
        self._emit(log_callback, "Generation Complete")
        self._emit(log_callback, "=" * 70)
        self._emit(log_callback, f"Duration : {stats['duration']}")
        self._emit(log_callback, f"Size     : {stats['size']}")
        self._emit(log_callback, f"Chapters : {len(chapters)}")
        self._emit(log_callback, f"Folder   : {project}")
        self._emit(log_callback, "")
        return True
