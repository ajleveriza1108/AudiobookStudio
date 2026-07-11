from pathlib import Path

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
)

from core.engine_service import EngineService


DEFAULT_TEXT = (
    "Welcome to Audiobook Studio. "
    "This is a preview of the currently selected voice. "
    "Adjust the speed and pitch until you are satisfied."
)


class VoicePreview(QWidget):

    preview_requested = Signal()

    def __init__(self):

        super().__init__()

        self.engine = None

        self.build()

    def build(self):

        layout = QVBoxLayout(self)

        title = QLabel("Voice Preview")

        title.setStyleSheet("""
font-size:20px;
font-weight:bold;
""")

        layout.addWidget(title)

        self.text = QTextEdit()

        self.text.setPlainText(

            DEFAULT_TEXT

        )

        layout.addWidget(

            self.text

        )

        self.voice = QComboBox()

        self.voice.addItem(

            "Engine Not Loaded"

        )

        layout.addWidget(

            self.voice

        )

        self.speed = QDoubleSpinBox()

        self.speed.setRange(

            0.50,

            2.00

        )

        self.speed.setSingleStep(

            0.05

        )

        self.speed.setValue(

            1.00

        )

        layout.addWidget(

            self.speed

        )

        self.pitch = QSpinBox()

        self.pitch.setRange(

            -12,

            12

        )

        layout.addWidget(

            self.pitch

        )

        self.preview = QPushButton(

            "Generate Preview"

        )

        layout.addWidget(

            self.preview

        )

        self.preview.clicked.connect(

            self.generate_preview

        )

    def load_engine(

        self,

        engine_name="kokoro"

    ):

        try:

            self.engine = EngineService.load(

                engine_name

            )

            self.voice.clear()

            voices = self.engine.available_voices()

            if voices:

                self.voice.addItems(

                    voices

                )

            else:

                self.voice.addItem(

                    "No Voices"

                )

            return True

        except Exception:

            self.engine = None

            self.voice.clear()

            self.voice.addItem(

                "Engine Not Loaded"

            )

            return False

    def generate_preview(self):

        if self.engine is None:

            if not self.load_engine():

                QMessageBox.warning(

                    self,

                    "Engine",

                    "Unable to load the selected engine."

                )

                return

        try:

            output = Path("Temp")

            output.mkdir(

                parents=True,

                exist_ok=True

            )

            preview = output / "voice_preview.wav"

            self.engine.speak(

                text=self.text.toPlainText(),

                output_file=preview,

                voice=self.voice.currentText(),

                speed=self.speed.value(),

                pitch=self.pitch.value()

            )

            QMessageBox.information(

                self,

                "Preview Ready",

                f"Saved to\n\n{preview}"

            )

        except Exception as e:

            QMessageBox.critical(

                self,

                "Error",

                str(e)

            )