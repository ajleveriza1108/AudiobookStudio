from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
)

from core.engine_service import EngineService
from core.paths import PATHS


DEFAULT_TEXT = (
    "Welcome to Audiobook Studio. This short passage lets you hear the selected "
    "narrator before generating the complete book."
)


class _PreviewWorker(QObject):
    ready = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, engine: str, voice: str, speed: float, pitch: float, text: str, output: Path):
        super().__init__()
        self.engine_name = engine
        self.voice = voice
        self.speed = speed
        self.pitch = pitch
        self.text = text
        self.output = output

    @Slot()
    def run(self):
        try:
            engine = EngineService.load(self.engine_name)
            engine.speak(
                text=self.text,
                output_file=self.output,
                voice=self.voice,
                speed=self.speed,
                pitch=self.pitch,
            )
            self.ready.emit(str(self.output))
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


class VoicePreviewDialog(QDialog):
    def __init__(self, engine="kokoro", voice="af_heart", speed=1.0, pitch=0.0, parent=None):
        super().__init__(parent)
        self.engine_name = str(engine)
        self.voice = str(voice)
        self.speed = float(speed)
        self.pitch = float(pitch)
        self.output_file: Path | None = None
        self.thread: QThread | None = None
        self.worker: _PreviewWorker | None = None
        self.player = None
        self.audio_output = None
        self.setWindowTitle("Voice Preview")
        self.resize(620, 420)
        self.build()

    def build(self):
        layout = QVBoxLayout(self)
        summary = QLabel(
            f"Engine: {self.engine_name}   •   Voice: {self.voice}   •   "
            f"Speed: {self.speed:.2f}×   •   Pitch: {self.pitch:g}"
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)

        self.text = QPlainTextEdit(DEFAULT_TEXT)
        self.text.setPlaceholderText("Enter a short passage to preview.")
        layout.addWidget(self.text, 1)

        row = QHBoxLayout()
        self.generate = QPushButton("Generate Preview")
        self.play = QPushButton("Play Preview")
        self.open_folder = QPushButton("Open Preview Folder")
        self.play.setEnabled(False)
        row.addWidget(self.generate)
        row.addWidget(self.play)
        row.addWidget(self.open_folder)
        layout.addLayout(row)

        self.status = QLabel("The first preview may take longer while the local engine loads.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)

        self.generate.clicked.connect(self.generate_preview)
        self.play.clicked.connect(self.play_preview)
        self.open_folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(PATHS.temp))))

    def generate_preview(self):
        content = self.text.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Voice Preview", "Enter a short passage to preview.")
            return
        if len(content) > 1500:
            QMessageBox.warning(self, "Voice Preview", "Keep the preview below 1,500 characters.")
            return
        if self.thread and self.thread.isRunning():
            return

        PATHS.temp.mkdir(parents=True, exist_ok=True)
        output = PATHS.temp / f"voice_preview_{datetime.now():%Y%m%d_%H%M%S}.wav"
        self.generate.setEnabled(False)
        self.play.setEnabled(False)
        self.status.setText("Generating the local voice preview…")

        self.thread = QThread(self)
        self.worker = _PreviewWorker(
            self.engine_name,
            self.voice,
            self.speed,
            self.pitch,
            content,
            output,
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.ready.connect(self._ready)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._thread_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _ready(self, filename: str):
        self.output_file = Path(filename)
        self.play.setEnabled(True)
        self.status.setText(f"Preview ready: {self.output_file.name}")
        self.play_preview()

    def _failed(self, message: str):
        self.status.setText("The preview could not be generated.")
        QMessageBox.critical(self, "Voice Preview", message)

    def _thread_finished(self):
        self.thread = None
        self.worker = None
        self.generate.setEnabled(True)

    def play_preview(self):
        if not self.output_file or not self.output_file.is_file():
            return
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            if self.player is None:
                self.audio_output = QAudioOutput(self)
                self.player = QMediaPlayer(self)
                self.player.setAudioOutput(self.audio_output)
            self.player.setSource(QUrl.fromLocalFile(str(self.output_file)))
            self.player.play()
        except Exception:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_file)))

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            QMessageBox.information(
                self,
                "Voice Preview",
                "Please wait for the current preview to finish before closing this window.",
            )
            event.ignore()
            return
        event.accept()
