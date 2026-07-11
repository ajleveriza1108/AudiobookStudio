from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
)

from core.voice_profiles import VoiceProfiles


class SettingsEngine(QGroupBox):

    DEFAULT_VOICES = [
        "af_heart",
        "af_bella",
        "af_nicole",
        "af_sarah",
        "af_sky",
        "am_adam",
        "am_michael",
        "bf_emma",
        "bm_george",
    ]

    def __init__(self):

        super().__init__("Engine")

        self.profiles = VoiceProfiles()

        layout = QFormLayout(self)

        layout.setContentsMargins(
            12,
            16,
            12,
            12
        )

        self.engine = QComboBox()

        self.engine.addItems([
            "kokoro",
            "piper",
            "xtts",
        ])

        self.profile = QComboBox()

        self.profile.addItems(
            self.profiles.names()
        )

        self.voice = QComboBox()

        layout.addRow(
            "Engine",
            self.engine,
        )

        layout.addRow(
            "Profile",
            self.profile,
        )

        layout.addRow(
            "Voice",
            self.voice,
        )

        self.engine.currentTextChanged.connect(
            self.reload_voices
        )

        self.profile.currentTextChanged.connect(
            self.load_profile
        )

        self.load_profile()

    def load_profile(self):

        profile = self.profiles.get(
            self.profile.currentText()
        )

        if profile:

            engine = profile.get(
                "engine",
                "kokoro",
            )

            index = self.engine.findText(engine)

            if index >= 0:

                self.engine.setCurrentIndex(index)

        self.reload_voices()

    def reload_voices(self):

        current = self.voice.currentText()

        self.voice.blockSignals(True)

        self.voice.clear()

        self.voice.addItems(
            self.DEFAULT_VOICES
        )

        if current in self.DEFAULT_VOICES:

            self.voice.setCurrentText(current)

        else:

            self.voice.setCurrentIndex(0)

        self.voice.blockSignals(False)

    def current_engine(self):

        return self.engine.currentText()

    def current_voice(self):

        voice = self.voice.currentText().strip()

        if not voice:

            return "af_heart"

        return voice