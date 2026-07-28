from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel

from core.voice_library import VoiceLibrary
from core.voice_profiles import VoiceProfiles
from engines.manager import EngineManager
from ui.compact_widgets import compact_form


VOICE_LABELS = {
    "af_heart": "Heart — Warm American Female",
    "af_alloy": "Alloy — Balanced American Female",
    "af_aoede": "Aoede — Expressive American Female",
    "af_bella": "Bella — Expressive American Female",
    "af_jessica": "Jessica — Clear American Female",
    "af_kore": "Kore — Calm American Female",
    "af_nicole": "Nicole — Clear American Female",
    "af_nova": "Nova — Bright American Female",
    "af_river": "River — Smooth American Female",
    "af_sarah": "Sarah — Natural American Female",
    "af_sky": "Sky — Bright American Female",
    "am_adam": "Adam — Clear American Male",
    "am_echo": "Echo — Steady American Male",
    "am_eric": "Eric — Natural American Male",
    "am_fenrir": "Fenrir — Deep American Male",
    "am_liam": "Liam — Friendly American Male",
    "am_michael": "Michael — Natural American Male",
    "am_onyx": "Onyx — Deep American Male",
    "am_puck": "Puck — Lively American Male",
    "am_santa": "Santa — Warm American Male",
    "bf_alice": "Alice — Clear British Female",
    "bf_emma": "Emma — Natural British Female",
    "bf_isabella": "Isabella — Refined British Female",
    "bf_lily": "Lily — Gentle British Female",
    "bm_daniel": "Daniel — Clear British Male",
    "bm_fable": "Fable — Storytelling British Male",
    "bm_george": "George — Mature British Male",
    "bm_lewis": "Lewis — Natural British Male",
}


class SettingsEngine(QGroupBox):
    availability_changed = Signal(bool, str)
    DEFAULT_VOICES = list(VOICE_LABELS)

    def __init__(self):
        super().__init__("Narration Engine")
        self.profiles = VoiceProfiles()
        self.voice_library = VoiceLibrary()
        self.manager = EngineManager()
        self._records: list[dict] = []

        layout = compact_form(QFormLayout(self))
        self.engine = QComboBox()
        self.profile = QComboBox()
        self.voice = QComboBox()
        self.engine_help = QLabel()
        self.engine_help.setWordWrap(True)
        self.engine_help.setObjectName("helpText")
        self.voice_help = QLabel()
        self.voice_help.setWordWrap(True)
        self.voice_help.setObjectName("helpText")

        layout.addRow("Engine", self.engine)
        layout.addRow("Profile", self.profile)
        layout.addRow("Voice", self.voice)
        layout.addRow("", self.engine_help)
        layout.addRow("", self.voice_help)

        self._load_engines()
        self.profile.addItems(self.profiles.names())
        self.engine.currentIndexChanged.connect(self.reload_voices)
        self.profile.currentTextChanged.connect(self.load_profile)
        self.load_profile()

    def _load_engines(self) -> None:
        selected = self.current_engine() if self.engine.count() else "kokoro"
        self.engine.clear()
        self.manager.reload()
        self._records = self.manager.available()
        for record in self._records:
            engine_id = str(record.get("name", ""))
            display = str(record.get("display_name") or engine_id)
            status = str(record.get("status", "Unavailable"))
            suffix = "Ready" if status == "Available" else status
            self.engine.addItem(f"{display} — {suffix}", engine_id)
            item = self.engine.model().item(self.engine.count() - 1)
            if item is not None and status != "Available":
                item.setEnabled(False)
        if not self.engine.count():
            self.engine.addItem("Kokoro — unavailable", "kokoro")
        self.set_engine(selected)

    def refresh_optional_engines(self) -> None:
        selected_engine = self.current_engine()
        selected_voice = self.current_voice()
        self._load_engines()
        self.set_engine(selected_engine)
        self.reload_voices()
        self.set_voice(selected_voice)

    def _current_record(self) -> dict:
        engine_id = self.current_engine()
        return next((item for item in self._records if str(item.get("name")) == engine_id), {})

    def is_available(self) -> bool:
        return str(self._current_record().get("status", "Unavailable")) == "Available"

    def status_summary(self) -> str:
        record = self._current_record()
        display = str(record.get("display_name") or self.current_engine().title())
        status = str(record.get("status", "Unavailable"))
        if status == "Available":
            backend = str(record.get("backend") or "CPU")
            return f"{display} ready • {backend} • loads on first use"
        missing = ", ".join(record.get("missing_dependencies", []) or [])
        if missing:
            return f"{display} unavailable • {missing}"
        return f"{display} {status.lower()}"

    def _update_engine_help(self) -> None:
        engine_id = self.current_engine()
        record = self._current_record()
        status = str(record.get("status", "Unavailable"))
        missing = ", ".join(record.get("missing_dependencies", []) or [])
        if engine_id == "chatterbox":
            if status == "Available":
                message = (
                    "Authorized local voice cloning is ready. Reference recordings remain in Voices/Cloned."
                )
            else:
                message = (
                    "Optional isolated voice engine not installed. Open Voice Studio to prepare profiles "
                    "or run install_voice_cloning.ps1."
                )
        elif status == "Available":
            message = "Fast local narration. The model loads only when preview or generation starts."
        elif status == "Disabled":
            message = "This optional engine is retained for future integration."
        else:
            message = "This engine is not ready on this computer."
            if missing:
                message += f" Missing: {missing}."
        self.engine_help.setText(message)
        self.availability_changed.emit(self.is_available(), self.status_summary())

    def load_profile(self):
        profile = self.profiles.get(self.profile.currentText())
        if profile:
            self.set_engine(str(profile.get("engine", "kokoro")))
        self.reload_voices()

    def reload_voices(self):
        current = self.current_voice()
        self.voice_library.reload()
        self.voice.blockSignals(True)
        self.voice.clear()
        engine = self.current_engine()
        if engine == "kokoro":
            for voice_id in self.DEFAULT_VOICES:
                self.voice.addItem(VOICE_LABELS.get(voice_id, voice_id), voice_id)
            self.voice_help.setText("Friendly names are shown; original Kokoro IDs remain internal.")
        elif engine == "chatterbox":
            for voice_id, label in self.voice_library.labels(engine="chatterbox"):
                self.voice.addItem(label, voice_id)
            if not self.voice.count():
                self.voice.addItem("Create a profile in Voice Studio", "")
            self.voice_help.setText("Use only recordings you own or are authorized to clone.")
        else:
            self.voice.addItem("No configured voices", "")
            self.voice_help.setText("")
        self.set_voice(current or ("af_heart" if engine == "kokoro" else ""))
        self.voice.blockSignals(False)
        self._update_engine_help()

    def current_engine(self):
        return str(self.engine.currentData() or "kokoro")

    def set_engine(self, engine_id: str):
        requested = str(engine_id)
        for index in range(self.engine.count()):
            if str(self.engine.itemData(index)) == requested:
                item = self.engine.model().item(index)
                if item is not None and item.isEnabled():
                    self.engine.setCurrentIndex(index)
                    self._update_engine_help()
                    return
                break
        for index in range(self.engine.count()):
            item = self.engine.model().item(index)
            if item is None or item.isEnabled():
                self.engine.setCurrentIndex(index)
                self._update_engine_help()
                return
        self.engine.setCurrentIndex(0)
        self._update_engine_help()

    def current_voice(self):
        return str(self.voice.currentData() or ("af_heart" if self.current_engine() == "kokoro" else ""))

    def set_voice(self, voice_id: str):
        for index in range(self.voice.count()):
            if str(self.voice.itemData(index)) == str(voice_id):
                self.voice.setCurrentIndex(index)
                return
        if self.voice.count():
            self.voice.setCurrentIndex(0)
