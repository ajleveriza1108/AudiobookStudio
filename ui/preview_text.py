from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class PreviewText(QWidget):
    DISPLAY_LIMIT = 200_000

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.title = QLabel("Narration Preview")
        self.title.setStyleSheet("font-size:16px;font-weight:700;padding:3px;")
        layout.addWidget(self.title)

        self.editor = QTextEdit()
        self.editor.setObjectName("bookPreview")
        self.editor.setReadOnly(True)
        self.editor.setPlaceholderText(
            "Import a PDF or EPUB to review the prepared narration text."
        )
        layout.addWidget(self.editor, 1)

    def set_text(self, text):
        value = str(text or "")
        if len(value) > self.DISPLAY_LIMIT:
            shown = value[: self.DISPLAY_LIMIT]
            shown += (
                "\n\n[Preview shortened for interface performance. "
                "The complete cleaned text will still be used for narration.]"
            )
            self.title.setText(f"Narration Preview — showing first {self.DISPLAY_LIMIT:,} characters")
            self.editor.setPlainText(shown)
        else:
            self.title.setText("Narration Preview")
            self.editor.setPlainText(value)

    def append(self, text):
        self.editor.append(str(text))

    def clear_text(self):
        self.title.setText("Narration Preview")
        self.editor.clear()

    def text(self):
        return self.editor.toPlainText()
