from __future__ import annotations

import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.optional_engines import chatterbox_runtime_ready
from core.paths import PATHS
from core.voice_library import SUPPORTED_LANGUAGES, VOICE_MODELS, VoiceLibrary


class VoiceStudioDialog(QDialog):
    profile_selected = Signal(str)
    profiles_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.library = VoiceLibrary()
        self._current_id = ""
        self.setWindowTitle("Voice Studio — Authorized Local Voices")
        self.resize(820, 560)
        self.setMinimumSize(680, 470)
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        heading = QLabel("Voice Studio")
        heading.setObjectName("dialogTitle")
        heading.setStyleSheet("font-size:18px;font-weight:700;")
        description = QLabel(
            "Create local voice profiles from recordings you own or have permission to use. "
            "Reference audio and generated speech stay on this computer."
        )
        description.setWordWrap(True)
        root.addWidget(heading)
        root.addWidget(description)

        status_row = QHBoxLayout()
        self.runtime_status = QLabel()
        self.runtime_status.setWordWrap(True)
        self.install_button = QPushButton("Install Optional Voice Engine")
        self.install_button.setToolTip(
            "Creates a separate voice-cloning environment. The verified Kokoro/OCR runtime is not changed."
        )
        status_row.addWidget(self.runtime_status, 1)
        status_row.addWidget(self.install_button)
        root.addLayout(status_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)
        list_layout.addWidget(QLabel("Saved profiles"))
        self.list = QListWidget()
        self.list.setMinimumWidth(220)
        list_layout.addWidget(self.list, 1)
        list_buttons = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.delete_button = QPushButton("Delete")
        list_buttons.addWidget(self.new_button)
        list_buttons.addWidget(self.delete_button)
        list_layout.addLayout(list_buttons)

        editor_page = QWidget()
        editor_layout = QVBoxLayout(editor_page)
        editor_layout.setContentsMargins(10, 0, 0, 0)
        editor_layout.setSpacing(8)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Example: Warm family narrator")
        self.model = QComboBox()
        for code, label in VOICE_MODELS.items():
            self.model.addItem(label, code)
        self.language = QComboBox()
        for code, label in SUPPORTED_LANGUAGES.items():
            self.language.addItem(label, code)
        self.sample = QLineEdit()
        self.sample.setReadOnly(True)
        self.sample.setPlaceholderText("Choose a clear single-speaker recording")
        self.browse = QPushButton("Choose Recording…")
        sample_row = QHBoxLayout()
        sample_row.setSpacing(6)
        sample_row.addWidget(self.sample, 1)
        sample_row.addWidget(self.browse)
        sample_widget = QWidget()
        sample_widget.setLayout(sample_row)
        self.audio_info = QLabel("Recommended: 10–60 seconds of clean speech with little background noise.")
        self.audio_info.setWordWrap(True)
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("Optional notes about the voice and permission source")
        self.notes.setMaximumHeight(86)
        self.permission = QCheckBox("I have permission to use this recording.")
        self.permission.setToolTip(
            "Use only recordings you own, recorded yourself, or are authorized to clone."
        )
        self.permission_help = QLabel(
            "Only use your own voice, an authorized speaker, or a properly licensed recording."
        )
        self.permission_help.setWordWrap(True)
        self.permission_help.setObjectName("helpText")
        form.addRow("Profile name", self.name)
        form.addRow("Model", self.model)
        form.addRow("Language", self.language)
        form.addRow("Reference", sample_widget)
        form.addRow("", self.audio_info)
        form.addRow("Notes", self.notes)
        editor_layout.addLayout(form)
        editor_layout.addWidget(self.permission)
        editor_layout.addWidget(self.permission_help)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("Save Profile")
        self.use_button = QPushButton("Use This Voice")
        self.use_button.setObjectName("primaryButton")
        action_row.addStretch(1)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.use_button)
        editor_layout.addLayout(action_row)
        editor_layout.addStretch(1)

        splitter.addWidget(list_page)
        splitter.addWidget(editor_page)
        splitter.setSizes([250, 540])
        root.addWidget(splitter, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.install_button.clicked.connect(self.install_runtime)
        self.new_button.clicked.connect(self.new_profile)
        self.delete_button.clicked.connect(self.delete_profile)
        self.browse.clicked.connect(self.choose_sample)
        self.save_button.clicked.connect(self.save_profile)
        self.use_button.clicked.connect(self.use_profile)
        self.list.currentItemChanged.connect(self.load_selected)
        self.model.currentIndexChanged.connect(self._model_changed)
        self._model_changed()

    def _set_runtime_status(self) -> None:
        if chatterbox_runtime_ready():
            self.runtime_status.setText(
                "Voice engine: installed • isolated runtime • model downloads on first use"
            )
            self.install_button.setText("Repair Voice Engine")
        else:
            self.runtime_status.setText(
                "Voice engine: optional module not installed. Profiles can be prepared now; "
                "Kokoro remains the default narrator."
            )
            self.install_button.setText("Install Optional Voice Engine")

    def refresh(self, select_id: str = "") -> None:
        self.library.reload()
        self._set_runtime_status()
        self.list.clear()
        profiles = self.library.all(authorized_only=False)
        for profile in profiles:
            label = SUPPORTED_LANGUAGES.get(profile.language, profile.language.upper())
            item = QListWidgetItem(f"{profile.name}\n{label}")
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            item.setToolTip(str(self.library.sample_path(profile)))
            self.list.addItem(item)
            if select_id and profile.id == select_id:
                self.list.setCurrentItem(item)
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
        elif not self.list.count():
            self.new_profile()

    def new_profile(self) -> None:
        self._current_id = ""
        self.name.clear()
        self.model.setCurrentIndex(max(0, self.model.findData("nano")))
        self.language.setCurrentIndex(max(0, self.language.findData("en")))
        self._model_changed()
        self.sample.clear()
        self.notes.clear()
        self.permission.setChecked(False)
        self.audio_info.setText(
            "Recommended: 10–60 seconds of clean speech with little background noise."
        )
        self.list.clearSelection()
        self.name.setFocus()

    def load_selected(self, current, _previous=None) -> None:
        if current is None:
            return
        profile_id = str(current.data(Qt.ItemDataRole.UserRole) or "")
        profile = self.library.get(profile_id)
        if profile is None:
            return
        self._current_id = profile.id
        self.name.setText(profile.name)
        model_index = self.model.findData(profile.model)
        self.model.setCurrentIndex(model_index if model_index >= 0 else 0)
        index = self.language.findData(profile.language)
        self.language.setCurrentIndex(index if index >= 0 else 0)
        self.sample.setText(str(self.library.sample_path(profile)))
        self.notes.setPlainText(profile.notes)
        self.permission.setChecked(profile.authorized)
        self._model_changed()
        self._describe_audio(Path(self.sample.text()))

    def _model_changed(self) -> None:
        selected = str(self.model.currentData() or "nano")
        multilingual = selected == "multilingual-v3"
        self.language.setEnabled(multilingual)
        if not multilingual:
            index = self.language.findData("en")
            self.language.setCurrentIndex(index if index >= 0 else 0)
            self.language.setToolTip("Nano and Turbo currently synthesize English.")
        else:
            self.language.setToolTip("Choose one of the supported multilingual languages.")

    def choose_sample(self) -> None:
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Authorized Voice Recording",
            "",
            "Audio (*.wav *.mp3 *.flac *.m4a *.ogg)",
        )
        if not file:
            return
        self.sample.setText(file)
        self._describe_audio(Path(file))
        if not self.name.text().strip():
            self.name.setText(Path(file).stem.replace("_", " ").strip().title())

    def _describe_audio(self, path: Path) -> None:
        try:
            import soundfile as sf

            info = sf.info(str(path))
            duration = float(info.frames) / max(1, int(info.samplerate))
            quality = "Good reference length" if 6 <= duration <= 120 else "Review reference length"
            self.audio_info.setText(
                f"{quality} • {duration:.1f} seconds • {info.samplerate:,} Hz • {info.channels} channel(s)"
            )
        except Exception:
            self.audio_info.setText(
                "The file will be validated when the profile is saved. Clear single-speaker audio works best."
            )

    def save_profile(self) -> None:
        try:
            if self._current_id:
                profile = self.library.update(
                    self._current_id,
                    name=self.name.text(),
                    language=str(self.language.currentData() or "en"),
                    notes=self.notes.toPlainText(),
                    model=str(self.model.currentData() or "nano"),
                    authorized=self.permission.isChecked(),
                    sample_file=self.sample.text(),
                )
            else:
                profile = self.library.add(
                    name=self.name.text(),
                    sample_file=self.sample.text(),
                    language=str(self.language.currentData() or "en"),
                    authorized=self.permission.isChecked(),
                    notes=self.notes.toPlainText(),
                    engine="chatterbox",
                    model=str(self.model.currentData() or "nano"),
                )
            self._current_id = profile.id
            self.profiles_changed.emit()
            self.refresh(profile.id)
        except Exception as error:
            QMessageBox.warning(self, "Voice Profile Not Saved", str(error))

    def delete_profile(self) -> None:
        if not self._current_id:
            return
        profile = self.library.get(self._current_id)
        if profile is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Voice Profile",
            f"Delete “{profile.name}” and its copied reference recording?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.library.remove(profile.id)
        self._current_id = ""
        self.profiles_changed.emit()
        self.refresh()

    def use_profile(self) -> None:
        if not self._current_id:
            QMessageBox.information(self, "Choose a Voice", "Save or select a voice profile first.")
            return
        profile = self.library.get(self._current_id)
        if profile is None or not profile.authorized:
            QMessageBox.warning(self, "Permission Required", "This voice profile is not authorized.")
            return
        if not chatterbox_runtime_ready():
            QMessageBox.information(
                self,
                "Optional Engine Not Installed",
                "The profile is saved. Install the optional voice engine before using it for narration.",
            )
            return
        self.profile_selected.emit(profile.id)
        self.accept()

    def install_runtime(self) -> None:
        script = PATHS.project_root / "install_voice_cloning.ps1"
        if not script.is_file():
            QMessageBox.warning(self, "Installer Missing", f"Could not find:\n{script}")
            return
        reply = QMessageBox.question(
            self,
            "Install Optional Voice Engine",
            "This creates a separate .voice-venv and downloads the Chatterbox package and model files. "
            "The verified Kokoro/OCR runtime will not be changed. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoExit",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-ProjectRoot",
                    str(PATHS.project_root),
                ],
                cwd=str(PATHS.project_root),
                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
            )
        except Exception as error:
            QMessageBox.warning(self, "Installer Could Not Start", str(error))
