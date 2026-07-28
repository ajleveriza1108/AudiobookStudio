from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.compact_widgets import compact_form


class SettingsExport(QGroupBox):
    def __init__(self):
        super().__init__("Export")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(5)

        self.export_wav = QCheckBox("WAV master")
        self.export_mp3 = QCheckBox("MP3")
        self.export_m4b = QCheckBox("M4B with chapters")
        self.overwrite = QCheckBox("Regenerate all sections")
        self.delete_chunks = QCheckBox("Delete sections after successful export")
        self.export_wav.setChecked(True)
        layout.addWidget(self.export_wav)
        layout.addWidget(self.export_mp3)
        layout.addWidget(self.export_m4b)

        basic_form = compact_form(QFormLayout())
        self.bitrate = QComboBox()
        self.bitrate.addItems(["96k", "128k", "160k", "192k", "256k", "320k"])
        self.bitrate.setCurrentText("192k")
        basic_form.addRow("Bitrate", self.bitrate)
        layout.addLayout(basic_form)

        self.advanced_button = QToolButton()
        self.advanced_button.setText("Advanced export options")
        self.advanced_button.setCheckable(True)
        self.advanced_button.setChecked(False)
        self.advanced_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advanced_button.setArrowType(Qt.ArrowType.RightArrow)
        layout.addWidget(self.advanced_button)

        self.advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_widget)
        advanced_layout.setContentsMargins(4, 0, 0, 0)
        advanced_layout.setSpacing(4)
        advanced_layout.addWidget(self.overwrite)
        advanced_layout.addWidget(self.delete_chunks)
        self.advanced_widget.setVisible(False)
        layout.addWidget(self.advanced_widget)

        self.metadata_button = QToolButton()
        self.metadata_button.setText("Metadata (optional)")
        self.metadata_button.setCheckable(True)
        self.metadata_button.setChecked(False)
        self.metadata_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.metadata_button.setArrowType(Qt.ArrowType.RightArrow)
        layout.addWidget(self.metadata_button)

        self.metadata_widget = QWidget()
        form = compact_form(QFormLayout(self.metadata_widget))
        self.title = QLineEdit()
        self.author = QLineEdit()
        self.narrator = QLineEdit()
        self.genre = QLineEdit("Audiobook")
        self.year = QLineEdit()
        self.description = QPlainTextEdit()
        self.description.setMaximumHeight(68)
        form.addRow("Title", self.title)
        form.addRow("Author", self.author)
        form.addRow("Narrator", self.narrator)
        form.addRow("Genre", self.genre)
        form.addRow("Year", self.year)
        form.addRow("Description", self.description)
        self.metadata_widget.setVisible(False)
        layout.addWidget(self.metadata_widget)
        layout.addStretch(1)

        self.advanced_button.toggled.connect(
            lambda shown: self._toggle_section(self.advanced_button, self.advanced_widget, shown)
        )
        self.metadata_button.toggled.connect(
            lambda shown: self._toggle_section(self.metadata_button, self.metadata_widget, shown)
        )

    @staticmethod
    def _toggle_section(button: QToolButton, widget: QWidget, shown: bool) -> None:
        widget.setVisible(bool(shown))
        button.setArrowType(Qt.ArrowType.DownArrow if shown else Qt.ArrowType.RightArrow)

    def options(self):
        return {
            "wav": self.export_wav.isChecked(),
            "mp3": self.export_mp3.isChecked(),
            "m4b": self.export_m4b.isChecked(),
            "overwrite": self.overwrite.isChecked(),
            "delete_chunks": self.delete_chunks.isChecked(),
            "bitrate": self.bitrate.currentText(),
        }

    def metadata(self) -> dict:
        return {
            "title": self.title.text().strip(),
            "author": self.author.text().strip(),
            "narrator": self.narrator.text().strip(),
            "genre": self.genre.text().strip() or "Audiobook",
            "year": self.year.text().strip(),
            "description": self.description.toPlainText().strip(),
        }

    def set_metadata(self, metadata: dict):
        if not metadata:
            return
        self.title.setText(str(metadata.get("title", "") or ""))
        self.author.setText(str(metadata.get("author", "") or ""))
        if not self.narrator.text().strip():
            self.narrator.setText(str(metadata.get("narrator", "") or ""))
        self.genre.setText(str(metadata.get("genre", "Audiobook") or "Audiobook"))
        self.year.setText(str(metadata.get("year", "") or ""))
        self.description.setPlainText(str(metadata.get("description", "") or ""))
