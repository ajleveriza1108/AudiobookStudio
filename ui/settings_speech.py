from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QGroupBox, QLabel, QPushButton, QSpinBox, QVBoxLayout

from ui.compact_widgets import compact_form


class SettingsSpeech(QGroupBox):
    pronunciation_requested = Signal()
    preview_requested = Signal()
    voice_studio_requested = Signal()

    def __init__(self):
        super().__init__("Narration Style")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 12, 8, 8)
        outer.setSpacing(6)
        form = compact_form(QFormLayout())

        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.50, 2.00)
        self.speed.setSingleStep(0.05)
        self.speed.setValue(1.00)
        self.speed.setSuffix("×")
        self.pitch = QSpinBox()
        self.pitch.setRange(-12, 12)
        self.pitch.setValue(0)
        self.pitch.setSuffix(" st")
        form.addRow("Speed", self.speed)
        form.addRow("Pitch", self.pitch)
        outer.addLayout(form)

        self.note = QLabel("Preview a short passage before generating a long book.")
        self.note.setWordWrap(True)
        self.note.setObjectName("helpText")
        outer.addWidget(self.note)

        self.preview_button = QPushButton("Voice Preview")
        self.pronunciation_button = QPushButton("Pronunciation")
        self.voice_studio_button = QPushButton("Voice Studio")
        outer.addWidget(self.preview_button)
        outer.addWidget(self.pronunciation_button)
        outer.addWidget(self.voice_studio_button)
        self.preview_button.clicked.connect(self.preview_requested.emit)
        self.pronunciation_button.clicked.connect(self.pronunciation_requested.emit)
        self.voice_studio_button.clicked.connect(self.voice_studio_requested.emit)

    def set_compact(self, compact: bool) -> None:
        self.note.setVisible(not compact)
        self.preview_button.setText("Preview" if compact else "Voice Preview")
        self.pronunciation_button.setText("Pronunciation" if compact else "Pronunciation Manager")

    def current_speed(self): return self.speed.value()
    def current_pitch(self): return self.pitch.value()
    def set_speed(self, value): self.speed.setValue(float(value))
    def set_pitch(self, value): self.pitch.setValue(int(value))
