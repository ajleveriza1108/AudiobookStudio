
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import fitz

from core.ocr import OCRService
from core.ocr_layout import OCRRegion, layout_ocr_regions


def _region(text, left, top, right, bottom, index):
    return OCRRegion(text, left, top, right, bottom, 0.97, index)


def test_dedication_form_pairs_labels_with_values_in_spoken_order():
    regions = [
        _region("1945 Remember When...", 180, 30, 470, 72, 0),
        _region("To:", 80, 165, 125, 190, 1),
        _region("Dad", 260, 158, 330, 190, 2),
        _region("From:", 80, 245, 145, 270, 3),
        _region("Dan + Diana", 260, 238, 410, 272, 4),
        _region("Date:", 80, 325, 140, 350, 5),
        _region("8-7-26", 260, 318, 350, 352, 6),
        _region(
            "The richness of life lies in the memories we have forgotten.",
            110,
            500,
            540,
            535,
            7,
        ),
    ]

    result = layout_ocr_regions(regions, page_width=620, page_height=800)

    assert result.mode == "form-fields-v2"
    assert result.text.startswith("Remember When, 1945.")
    assert "\n\nTo Dad.\n\n" in result.text
    assert "\n\nFrom Dan and Diana.\n\n" in result.text
    assert "\n\nDate: August 7, 2026.\n\n" in result.text
    assert "Dad To" not in result.text
    assert result.text.index("Remember When, 1945.") < result.text.index("To Dad.")
    assert result.text.index("To Dad.") < result.text.index("From Dan and Diana.")
    assert result.text.index("From Dan and Diana.") < result.text.index("Date: August 7, 2026.")


def test_legacy_1945_hardcoded_profile_is_removed():
    from pathlib import Path

    profile_file = (
        Path(__file__).resolve().parents[1]
        / "Resources"
        / "OCRCorrections"
        / "remember_when_1945.json"
    )
    assert not profile_file.exists()


def test_complete_cache_without_new_verified_profile_is_rejected(tmp_path, monkeypatch):
    source = tmp_path / "Remember_When_1945.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "generic OCR content with enough words to pass validation")
    document.save(source)
    document.close()

    cache = tmp_path / "cache"
    cache.mkdir()
    text = "generic OCR content with enough words to pass validation"
    manifest = {
        "schema": OCRService.CACHE_SCHEMA,
        "layout_schema": OCRService.LAYOUT_SCHEMA,
        "engine_preference": OCRService.engine_preference(),
        "backend": "RapidOCR",
        "complete": True,
        "source_page_count": 1,
        "pages": 1,
        "ocr_pages": 1,
        "embedded_pages": 0,
        "structured_pages": 0,
        "timeline_pages": 0,
        "multi_column_pages": 0,
        "low_confidence_pages": 0,
        "advanced_pages": 0,
        "fallback_pages": 0,
        "correction_profile": "",
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "page_word_counts": [9],
    }
    (cache / "ocr_text.txt").write_text(text, encoding="utf-8")
    (cache / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    fake_profile = SimpleNamespace(profile_id="new-verified-profile")
    import core.ocr as ocr_module

    monkeypatch.setattr(OCRService, "cache_folder", classmethod(lambda cls, path: cache))
    monkeypatch.setattr(
        ocr_module,
        "find_correction_profile",
        lambda source, page_count: fake_profile,
    )

    assert OCRService.cached_text(source) is None


def test_version_contract_r1177():
    from core.version import BUILD, VERSION

    assert "R1.17.7" in VERSION
    assert BUILD == 1775
