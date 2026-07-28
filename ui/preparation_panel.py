from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from core.book_preparation import format_preparation_report


class PreparationPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.report: dict = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.summary = QLabel("Import a book to create a preparation report.")
        self.summary.setWordWrap(True)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Preparation findings will appear here.")
        layout.addWidget(self.summary)
        layout.addWidget(self.text, 1)

    def set_report(self, report: dict):
        self.report = dict(report or {})
        summary = self.report.get("summary", {})
        warnings = sum(1 for item in self.report.get("issues", []) if item.get("severity") == "warning")
        notices = len(self.report.get("issues", [])) - warnings
        structured = int(summary.get("structured_ocr_pages", 0) or 0)
        layout_note = f" • {structured} structured OCR page(s)" if structured else ""
        self.summary.setText(
            f"{int(summary.get('words', 0)):,} words • "
            f"{int(summary.get('chapters', 0))} detected chapter(s)"
            f"{layout_note} • {warnings} warning(s) • {notices} notice(s)"
        )
        self.text.setPlainText(format_preparation_report(self.report))

    def warning_count(self) -> int:
        return sum(1 for item in self.report.get("issues", []) if item.get("severity") == "warning")

    def clear(self):
        self.report = {}
        self.summary.setText("Import a book to create a preparation report.")
        self.text.clear()
