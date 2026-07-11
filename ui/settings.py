from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
)

from ui.settings_engine import SettingsEngine
from ui.settings_speech import SettingsSpeech
from ui.settings_export import SettingsExport
from ui.settings_book import SettingsBook
from ui.settings_output import SettingsOutput
from ui.settings_generate import SettingsGenerate

from ui.layouts.button_state import ButtonState


class SettingsPanel(QWidget):

    book_selected = Signal(str)

    output_selected = Signal(str)

    generate_requested = Signal()

    settings_changed = Signal()

    def __init__(self):

        super().__init__()
        
        self.setMinimumWidth(
            450
        )

        self.build()

    def build(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(

            12,

            12,

            12,

            12,

        )

        root.setSpacing(

            12

        )

        title = QLabel(

            "Settings"

        )

        title.setStyleSheet("""

font-size:22px;

font-weight:bold;

padding:4px;

""")

        root.addWidget(

            title

        )

        grid = QGridLayout()

        grid.setHorizontalSpacing(

            12

        )

        grid.setVerticalSpacing(

            12

        )

        self.engine = SettingsEngine()

        self.speech = SettingsSpeech()

        self.export = SettingsExport()

        grid.addWidget(

            self.engine,

            0,

            0,

        )

        grid.addWidget(

            self.speech,

            0,

            1,

        )

        grid.addWidget(

            self.export,

            0,

            2,

        )

        # Removed the rigid column stretches here so Qt auto-calculates widths

        root.addLayout(

            grid

        )

        bottom = QGridLayout()

        bottom.setHorizontalSpacing(

            12

        )

        bottom.setVerticalSpacing(

            12

        )

        self.book = SettingsBook()

        self.output = SettingsOutput()

        bottom.addWidget(

            self.book,

            0,

            0,

        )

        bottom.addWidget(

            self.output,

            0,

            1,

        )

        bottom.setColumnStretch(

            0,

            1,

        )

        bottom.setColumnStretch(

            1,

            1,

        )

        root.addLayout(

            bottom

        )

        self.generate = SettingsGenerate()

        root.addWidget(

            self.generate

        )

        self.button_state = ButtonState(

            self.generate

        )

        self.book.book_selected.connect(

            self._book_selected

        )

        self.output.output_selected.connect(

            self._output_selected

        )

        self.generate.generate_requested.connect(

            self.generate_requested.emit

        )

    def _book_selected(

        self,

        file,

    ):

        self.button_state.set_book(

            True

        )

        self.book_selected.emit(

            file

        )

    def _output_selected(

        self,

        folder,

    ):

        self.button_state.set_output(

            True

        )

        self.output_selected.emit(

            folder

        )

    @property
    def voice(self):
        return self.engine.voice

    @property
    def profile(self):
        return self.engine.profile

    @property
    def speed(self):
        return self.speech.speed

    @property
    def pitch(self):
        return self.speech.pitch

    @property
    def export_wav(self):
        return self.export.export_wav

    @property
    def export_mp3(self):
        return self.export.export_mp3

    @property
    def export_m4b(self):
        return self.export.export_m4b

    @property
    def overwrite(self):
        return self.export.overwrite

    @property
    def delete_chunks(self):
        return self.export.delete_chunks

    def export_options(self):
        return self.export.options()

    def current_engine(self):
        return self.engine.current_engine()

    def current_voice(self):
        return self.engine.current_voice()

    def current_speed(self):
        return self.speech.current_speed()

    def current_pitch(self):
        return self.speech.current_pitch()

    def reload_voices(self):

        self.engine.reload_voices()

        self.settings_changed.emit()