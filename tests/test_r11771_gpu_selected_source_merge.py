from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_exact_selected_pdf_and_gpu_features_are_both_present():
    defaults = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert defaults["processing_device"] == "auto"
    assert defaults["gpu_runtime_enabled"] is True
    assert defaults["removed_books"] == []

    project = (ROOT / "core" / "project.py").read_text(encoding="utf-8")
    controller = (ROOT / "controllers" / "generation_controller.py").read_text(encoding="utf-8")
    launcher = (ROOT / "launch_audiobook_studio.ps1").read_text(encoding="utf-8-sig")

    assert "expected_source_sha256" in project
    assert "Selected Source.json" in project
    assert "source_sha256" in controller
    assert ".gpu-venv\\Scripts\\python.exe" in launcher
    assert 'AUDIOBOOK_STUDIO_DEVICE = "cuda"' in launcher
    assert 'AUDIOBOOK_STUDIO_DEVICE = "cpu"' in launcher


def test_hardcoded_remember_when_profile_is_absent():
    assert not (ROOT / "Resources" / "OCRCorrections" / "remember_when_1945.json").exists()


def test_selected_source_persistence_and_removed_book_tombstones_are_present():
    config = (ROOT / "core" / "config.py").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    sidebar = (ROOT / "ui" / "sidebar.py").read_text(encoding="utf-8")
    assert "remove_recent_book" in config
    assert "is_book_removed" in config
    assert "removed_books" in config
    assert "is_book_removed(last_book)" in app
    assert "book_removed" in sidebar


def test_runtime_scans_exclude_machine_environments():
    source = (ROOT / "tests" / "test_runtime_repair_r14.py").read_text(encoding="utf-8")
    assert '".gpu-venv"' in source
    assert '".advanced-ocr-venv"' in source
    assert '"site-packages"' in source
