from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QScrollArea, QTabWidget, QVBoxLayout, QWidget

from core.parser import parse_book
from core.pronunciation import PronunciationDictionary
from ui.layouts.button_state import ButtonState
from ui.pronunciation_manager import PronunciationManagerDialog
from ui.settings_book import SettingsBook
from ui.settings_engine import SettingsEngine
from ui.settings_export import SettingsExport
from ui.settings_generate import SettingsGenerate
from ui.settings_output import SettingsOutput
from ui.settings_speech import SettingsSpeech
from ui.voice_preview import VoicePreviewDialog
from ui.voice_studio import VoiceStudioDialog


class SettingsPanel(QWidget):
    book_selected = Signal(str)
    output_selected = Signal(str)
    generate_requested = Signal()
    settings_changed = Signal()
    engine_status_changed = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self._generation_running = False
        self._pronunciation_dialog = None
        self._preview_dialog = None
        self._voice_studio_dialog = None
        self.build()

    @staticmethod
    def _scroll_tab(*widgets):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        return scroll

    def build(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(6, 6, 6, 6)
        self.root.setSpacing(5)
        self.title = QLabel("Production Settings")
        self.title.setObjectName("panelTitle")
        self.title.setStyleSheet("font-size:17px;font-weight:700;padding:2px;")
        self.root.addWidget(self.title)

        self.engine = SettingsEngine(); self.speech = SettingsSpeech(); self.export = SettingsExport()
        self.book = SettingsBook(); self.output = SettingsOutput()
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.addTab(self._scroll_tab(self.book, self.output), "Book")
        self.tabs.addTab(self._scroll_tab(self.engine, self.speech), "Narrator")
        self.tabs.addTab(self._scroll_tab(self.export), "Export")
        self.root.addWidget(self.tabs, 1)
        self.generate = SettingsGenerate(); self.root.addWidget(self.generate)

        self.button_state = ButtonState(self.generate)
        self.button_state.set_output(bool(self.output.current_output()))
        self.button_state.set_engine(self.engine.is_available())
        self.book.book_selected.connect(self._book_selected)
        self.output.output_selected.connect(self._output_selected)
        self.generate.generate_requested.connect(self.generate_requested.emit)
        self.speech.pronunciation_requested.connect(self.open_pronunciation_manager)
        self.speech.preview_requested.connect(self.open_voice_preview)
        self.speech.voice_studio_requested.connect(self.open_voice_studio)
        self.engine.availability_changed.connect(self._engine_state_changed)

        controls = [self.engine.engine, self.engine.profile, self.engine.voice, self.speech.speed, self.speech.pitch,
                    self.export.export_wav, self.export.export_mp3, self.export.export_m4b, self.export.overwrite,
                    self.export.delete_chunks, self.export.bitrate, self.export.title, self.export.author,
                    self.export.narrator, self.export.genre, self.export.year, self.export.description]
        for control in controls:
            signal = next((getattr(control, name, None) for name in ("currentIndexChanged","valueChanged","toggled","textChanged") if getattr(control, name, None) is not None), None)
            if signal is not None: signal.connect(lambda *_: self.settings_changed.emit())
        self._engine_state_changed(self.engine.is_available(), self.engine.status_summary())

    def set_compact(self, compact: bool) -> None:
        self.title.setText("Settings" if compact else "Production Settings")
        self.speech.set_compact(compact)
        self.generate.button.setMinimumHeight(42 if compact else 50)

    def _refresh_generate(self):
        ready = not self._generation_running and self.button_state.ready()
        self.generate.set_enabled(ready)
        if not self.button_state.engine: tip = "Install or repair the selected narration engine."
        elif not self.button_state.book: tip = "Import a PDF or EPUB first."
        elif not self.button_state.output: tip = "Choose an output folder first."
        else: tip = "Generate the selected book with the current settings."
        self.generate.button.setToolTip(tip)

    def _engine_state_changed(self, available, message):
        self.button_state.set_engine(available); self._refresh_generate(); self.engine_status_changed.emit(bool(available), str(message))
    def _book_selected(self, file): self.set_book(file); self.book_selected.emit(file)
    def _output_selected(self, folder): self.set_output(folder); self.output_selected.emit(folder)
    def set_book(self, file):
        self.book.set_book(file)
        try: self.export.set_metadata(parse_book(file))
        except Exception: pass
        self.button_state.book = bool(file); self._refresh_generate()
    def clear_book(self): self.book.set_book(""); self.button_state.book=False; self._refresh_generate()
    def set_output(self, folder): self.output.set_output(folder); self.button_state.output=bool(folder); self._refresh_generate()
    def set_generation_running(self, running):
        self._generation_running=bool(running); self._refresh_generate(); self.tabs.setEnabled(not running)
        self.book.button.setEnabled(not running); self.output.button.setEnabled(not running)
        self.speech.preview_button.setEnabled(not running and self.engine.is_available())
        self.speech.pronunciation_button.setEnabled(not running); self.speech.voice_studio_button.setEnabled(not running)
    def open_pronunciation_manager(self):
        self._pronunciation_dialog=PronunciationManagerDialog(self); self._pronunciation_dialog.rules_changed.connect(self.settings_changed.emit); self._pronunciation_dialog.exec(); self._pronunciation_dialog=None
    def open_voice_preview(self):
        if not self.engine.is_available(): return
        self._preview_dialog=VoicePreviewDialog(engine=self.current_engine(), voice=self.current_voice(), speed=self.current_speed(), pitch=self.current_pitch(), parent=self)
        self._preview_dialog.exec(); self._preview_dialog=None
    def open_voice_studio(self):
        self._voice_studio_dialog=VoiceStudioDialog(self)
        self._voice_studio_dialog.profiles_changed.connect(self.engine.refresh_optional_engines)
        self._voice_studio_dialog.profile_selected.connect(self._use_voice_profile)
        self._voice_studio_dialog.exec(); self.engine.refresh_optional_engines(); self._voice_studio_dialog=None
    def _use_voice_profile(self, profile_id):
        self.engine.refresh_optional_engines(); self.engine.set_engine("chatterbox"); self.engine.reload_voices(); self.engine.set_voice(profile_id); self.tabs.setCurrentIndex(1); self.settings_changed.emit()
    @property
    def voice(self): return self.engine.voice
    @property
    def profile(self): return self.engine.profile
    @property
    def speed(self): return self.speech.speed
    @property
    def pitch(self): return self.speech.pitch
    @property
    def export_wav(self): return self.export.export_wav
    @property
    def export_mp3(self): return self.export.export_mp3
    @property
    def export_m4b(self): return self.export.export_m4b
    @property
    def overwrite(self): return self.export.overwrite
    @property
    def delete_chunks(self): return self.export.delete_chunks
    def export_options(self): return self.export.options()
    def metadata_overrides(self): return self.export.metadata()
    def pronunciation_rules(self): return PronunciationDictionary().list_rules()
    def current_engine(self): return self.engine.current_engine()
    def set_engine(self, engine_id): self.engine.set_engine(engine_id)
    def current_voice(self): return self.engine.current_voice()
    def set_voice(self, voice_id): self.engine.set_voice(voice_id)
    def current_speed(self): return self.speech.current_speed()
    def current_pitch(self): return self.speech.current_pitch()
    def reload_voices(self): self.engine.reload_voices(); self.settings_changed.emit()
    def engine_available(self): return self.engine.is_available()
    def engine_status_text(self): return self.engine.status_summary()
