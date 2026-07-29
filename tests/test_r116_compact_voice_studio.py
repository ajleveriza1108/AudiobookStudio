from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.voice_library import SUPPORTED_LANGUAGES, VOICE_MODELS, VoiceLibrary


ROOT = Path(__file__).resolve().parents[1]


def test_voice_library_requires_permission_and_preserves_model(tmp_path):
    sample = tmp_path / "authorized.wav"
    sample.write_bytes(b"RIFF" + b"\0" * 100)
    library = VoiceLibrary(tmp_path / "voices")

    with pytest.raises(ValueError, match="Permission confirmation"):
        library.add(name="Test", sample_file=sample, authorized=False)

    profile = library.add(
        name="Authorized Narrator",
        sample_file=sample,
        language="fr",
        authorized=True,
        model="multilingual-v3",
    )
    assert profile.model == "multilingual-v3"
    assert profile.language == "fr"
    assert library.sample_path(profile).is_file()

    updated = library.update(profile.id, model="nano", language="de")
    assert updated.model == "nano"
    assert updated.language == "en"

    payload = json.loads(library.index.read_text(encoding="utf-8"))
    assert payload["profiles"][0]["authorized"] is True
    assert payload["profiles"][0]["model"] == "nano"


def test_voice_models_and_languages_match_supported_ui_contract():
    assert set(VOICE_MODELS) == {"nano", "turbo", "multilingual-v3"}
    assert "en" in SUPPORTED_LANGUAGES
    assert "fr" in SUPPORTED_LANGUAGES
    assert "zh" in SUPPORTED_LANGUAGES
    assert "cs" not in SUPPORTED_LANGUAGES


def test_compact_gui_source_contracts():
    responsive = (ROOT / "ui" / "responsive_controller.py").read_text(encoding="utf-8")
    settings_export = (ROOT / "ui" / "settings_export.py").read_text(encoding="utf-8")
    chapter_editor = (ROOT / "ui" / "chapter_editor.py").read_text(encoding="utf-8")
    batch_queue = (ROOT / "ui" / "batch_queue.py").read_text(encoding="utf-8")
    voice_studio = (ROOT / "ui" / "voice_studio.py").read_text(encoding="utf-8")
    initializer = (ROOT / "ui" / "window_initializer.py").read_text(encoding="utf-8")

    assert 'LayoutMode("focus"' in responsive
    assert "_effective_side_panels" in responsive
    assert "one side panel at a time" in responsive.lower()
    assert "Advanced export options" in settings_export
    assert "Metadata (optional)" in settings_export
    assert "QGridLayout" in chapter_editor
    assert "QGridLayout" in batch_queue
    assert "self.permission.setWordWrap" not in voice_studio
    assert "setMinimumSize(900, 620)" in initializer
    assert "1600" not in initializer


def test_optional_voice_runtime_is_isolated_and_marked_ready():
    installer = (ROOT / "install_voice_cloning.ps1").read_text(encoding="utf-8")
    optional = (ROOT / "core" / "optional_engines.py").read_text(encoding="utf-8")
    worker = (ROOT / "Scripts" / "chatterbox_worker.py").read_text(encoding="utf-8")

    assert '".voice-venv"' in installer
    assert "-3.11" in installer
    assert "chatterbox-tts==0.1.7" in installer
    assert ".audiobookstudio_chatterbox_ready.json" in installer
    assert ".audiobookstudio_chatterbox_ready.json" in optional
    assert 'request = {}' in worker
    assert 'audio_prompt_path' in worker


def test_r116_version_and_theme_are_compact():
    version = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    theme = (ROOT / "ui" / "theme_manager.py").read_text(encoding="utf-8")
    assert "R1." in version
    assert "BUILD =" in version
    assert 'font-size:9pt' in theme
    assert 'min-height:25px' in theme
