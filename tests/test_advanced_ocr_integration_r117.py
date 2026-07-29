from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def test_advanced_ocr_ui_is_toggle_gated_and_compact():
    source = read("ui/settings_advanced_ocr.py")
    assert 'QCheckBox("Use Unlimited-OCR for difficult scanned pages")' in source
    assert 'QPushButton("Check Laptop")' in source
    assert 'QPushButton("Install Module")' in source
    assert "QGridLayout" in source
    assert "check_and_record" in source
    assert 'config.set("advanced_ocr_enabled", False)' in source


def test_advanced_ocr_isolated_runtime_contract():
    optional = read("core/optional_engines.py")
    installer = read("install_advanced_ocr.ps1")
    assert '".advanced-ocr-venv"' in optional
    assert ".audiobookstudio_unlimited_ocr_ready.json" in optional
    assert 'PATHS.models / "Unlimited-OCR"' in optional
    assert 'torch==2.10.0' in installer
    assert 'torchvision==0.25.0' in installer
    assert 'transformers==4.57.1' in installer
    assert 'https://download.pytorch.org/whl/cu129' in installer
    assert "-AllowExperimental" in installer


def test_ocr_service_has_automatic_standard_fallback():
    source = read("core/ocr.py")
    assert 'backend == "Unlimited-OCR"' in source
    assert "base_availability" in source
    assert "advanced_fallback" in source
    assert "standard OCR fallback was used" in source
    assert '"engine_preference"' in source


def test_worker_is_local_only_and_has_generation_guards():
    worker = read("Scripts/advanced_ocr_worker.py")
    downloader = read("Scripts/download_unlimited_ocr.py")
    assert "local_files_only=True" in worker
    assert "no_repeat_ngram_size=35" in worker
    assert "ngram_window=128" in worker
    assert "max_length=16384" in worker
    assert "d549bb9d6a055dbe291408916d66acc2cd5920f6" in downloader
    assert "2bc48a7a110061ea58fff65d3169367eebe3aee371ca6968dc2219c1b2855fc6" in downloader
