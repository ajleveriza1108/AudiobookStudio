from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.book_preparation import analyze_book_text, scanned_pdf_report
from core.chapters import detect_chapters, full_book_chapter
from core.cleaner import clean_text
from core.engine_service import EngineService
from core.estimate import estimate_duration
from core.ocr import OCRService
from core.parser import ScannedPDFError, extract_book_text, parse_book, pdf_text_diagnostics
from engines.manager import EngineManager
from ui.chapter_editor import ChapterEditor
from ui.preparation_panel import PreparationPanel
from ui.preview_cover import PreviewCover
from ui.preview_metadata import PreviewMetadata
from ui.preview_text import PreviewText


class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.current_book: Path | None = None
        self.cleaned_text = ""
        self.raw_text = ""
        self.report: dict = {}
        self.requires_ocr = False
        self.text_ready = False
        self.build_ui()

    def build_ui(self):
        self.root = QVBoxLayout(self)
        root = self.root
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self.title = QLabel("No Book Selected")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:20px;font-weight:700;padding:2px;")
        self.title.setWordWrap(True)
        self.title.setMinimumHeight(36)
        self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        root.addWidget(self.title)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        root.addWidget(self.tabs, 1)

        overview = QWidget()
        overview_layout = QHBoxLayout(overview)
        overview_layout.setContentsMargins(6, 6, 6, 6)
        overview_layout.setSpacing(8)
        self.overview_layout = overview_layout
        self.cover = PreviewCover()
        self.meta = PreviewMetadata()
        overview_layout.addWidget(self.cover)
        overview_layout.addWidget(self.meta, 1)

        self.preview = PreviewText()
        self.preparation = PreparationPanel()
        self.chapter_editor = ChapterEditor()

        self.tabs.addTab(overview, "Overview")
        self.tabs.addTab(self.preview, "Cleaned Text")
        self.tabs.addTab(self.preparation, "Preparation")
        self.tabs.addTab(self.chapter_editor, "Chapters")

    def set_compact(self, compact: bool) -> None:
        self.root.setContentsMargins(4 if compact else 8, 4 if compact else 8, 4 if compact else 8, 4 if compact else 8)
        self.title.setStyleSheet(
            "font-size:17px;font-weight:700;padding:1px;" if compact
            else "font-size:20px;font-weight:700;padding:2px;"
        )
        self.title.setMinimumHeight(28 if compact else 36)
        self.cover.setVisible(not compact)

    def _set_engine_metadata(self) -> None:
        self.meta.set_value("Engine", "Kokoro")
        if EngineService.loaded():
            backend = f"{EngineService.backend()} • loaded"
        else:
            record = next(
                (
                    item
                    for item in EngineManager().available()
                    if str(item.get("name")) == "kokoro"
                ),
                {},
            )
            if record.get("status") == "Available":
                backend = f"{record.get('backend', 'CPU')} • installed • loads on first use"
            else:
                missing = ", ".join(record.get("missing_dependencies", []) or [])
                backend = f"Unavailable{f' • missing {missing}' if missing else ''}"
        self.meta.set_value("Backend", backend)

    def _load_scanned_pdf_state(self, error: Exception) -> None:
        self.requires_ocr = True
        self.text_ready = False
        self.raw_text = ""
        self.cleaned_text = ""

        details = pdf_text_diagnostics(self.current_book) if self.current_book else {}
        availability = OCRService.availability()
        pages = int(details.get("pages") or 0)
        self.report = scanned_pdf_report(
            self.current_book or "",
            pages=pages,
            ocr_available=availability.available,
            ocr_backend=availability.backend,
        )

        self.meta.set_value("Text", "Scanned page images")
        self.meta.set_value("Words", "Pending offline OCR")
        self.meta.set_value("Characters", "Pending offline OCR")
        self.meta.set_value("Chapters", "1 • Full Book")
        self.meta.set_value("Duration", "Calculated after OCR")
        self.meta.set_value("Estimated Size", "Calculated after OCR")
        self.meta.set_value(
            "Preparation",
            f"OCR ready • {availability.backend}" if availability.available else "OCR installation required",
        )

        if availability.available:
            message = (
                "Scanned PDF detected\n\n"
                "This file contains photographed or scanned page images instead of selectable text. "
                "That is supported. When you click Generate Audiobook, Audiobook Studio will:\n\n"
                "1. Run offline OCR page by page.\n"
                "2. Save the recognized text in the local OCR cache.\n"
                "3. Treat the book as one Full Book section when no headings are recognized.\n"
                "4. Detect chapter headings automatically when OCR can read them.\n"
                "5. Continue into Kokoro narration without changing the original PDF.\n\n"
                f"OCR engine: {availability.backend}\n"
                f"Pages to read: {pages or 'Unknown'}"
            )
        else:
            message = (
                "Scanned PDF detected\n\n"
                "This file contains page images and needs offline OCR before narration.\n\n"
                "Close Audiobook Studio, run install_dependencies.ps1, then reopen this book. "
                "The installer adds RapidOCR and ONNX Runtime.\n\n"
                f"Technical detail: {error}"
            )

        self.preview.set_text(message)
        self.preparation.set_report(self.report)
        self.chapter_editor.load([full_book_chapter("", virtual=True)])

    def load_book(self, file):
        self.current_book = Path(file).expanduser().resolve()
        self.title.setText(self.current_book.stem)
        self.meta.clear_values()
        self.preview.set_text("Reading and preparing book text…")
        self.preparation.clear()
        self.chapter_editor.clear()
        self.requires_ocr = False
        self.text_ready = False

        try:
            meta = parse_book(self.current_book)
            self.title.setText(str(meta.get("title") or self.current_book.stem))
            self.meta.set_value("Author", meta.get("author", "Unknown"))
            self.meta.set_value("Pages", meta.get("pages", "Unknown"))
            self.meta.set_value("Language", meta.get("language", "Unknown"))
            self.meta.set_value("Type", meta.get("type", "Unknown"))
        except Exception as error:
            self.meta.set_value("Metadata", f"Needs review: {error}")

        try:
            diagnostics: dict = {}
            self.raw_text = extract_book_text(self.current_book, diagnostics=diagnostics)
            self.cleaned_text = clean_text(self.raw_text)
            if not self.cleaned_text.strip():
                raise ScannedPDFError(
                    "No readable narration text remained after preparation."
                )

            self.requires_ocr = bool(diagnostics.get("ocr_used"))
            self.text_ready = True
            chapters = detect_chapters(self.cleaned_text)
            self.report = analyze_book_text(
                self.raw_text, self.cleaned_text, self.current_book, diagnostics=diagnostics
            )
            hours, minutes = estimate_duration(self.cleaned_text)

            self.meta.set_value("Duration", f"{hours}h {minutes}m")
            self.meta.set_value("Words", f"{len(self.cleaned_text.split()):,}")
            self.meta.set_value("Characters", f"{len(self.cleaned_text):,}")
            self.meta.set_value("Chapters", len(chapters))
            self.meta.set_value("Estimated Size", f"{round((len(self.cleaned_text.split()) / 155) * 1.45, 1)} MB")
            if diagnostics.get("ocr_used"):
                source = "Cached OCR" if diagnostics.get("ocr_cache_hit") else "Offline OCR"
                structured = int(diagnostics.get("structured_pages") or 0)
                timeline = int(diagnostics.get("timeline_pages") or 0)
                layout_note = ""
                if structured:
                    layout_note = f" • layout-aware ({structured} page(s)"
                    if timeline:
                        layout_note += f", {timeline} timeline"
                    layout_note += ")"
                self.meta.set_value(
                    "Text",
                    f"{source} • {diagnostics.get('ocr_backend', 'Local')}{layout_note}",
                )
            self.meta.set_value("Preparation", "Ready" if self.report.get("ready") else "Review recommended")
            self.preview.set_text(self.cleaned_text)
            self.preparation.set_report(self.report)
            self.chapter_editor.load(chapters)
        except ScannedPDFError as error:
            self._load_scanned_pdf_state(error)
        except Exception as error:
            self.raw_text = ""
            self.cleaned_text = ""
            self.report = {}
            self.requires_ocr = False
            self.text_ready = False
            self.preview.set_text(
                "Audiobook Studio could not extract readable text from this book.\n\n"
                f"Details: {error}"
            )
            self.meta.set_value("Text", "Unavailable")

        self._set_engine_metadata()
        self.cover.load_cover(self.current_book)

    def chapter_plan(self) -> list[dict]:
        return self.chapter_editor.plan()

    def included_chapter_count(self) -> int:
        return self.chapter_editor.included_count()

    def preparation_warning_count(self) -> int:
        return self.preparation.warning_count()

    def preparation_report(self) -> dict:
        return dict(self.report)

    def is_ocr_required(self) -> bool:
        return bool(self.requires_ocr and not self.text_ready)

    def clear(self):
        self.current_book = None
        self.cleaned_text = ""
        self.raw_text = ""
        self.report = {}
        self.requires_ocr = False
        self.text_ready = False
        self.title.setText("No Book Selected")
        self.meta.clear_values()
        self.preview.clear_text()
        self.preparation.clear()
        self.chapter_editor.clear()
        self.cover.clear_cover()
