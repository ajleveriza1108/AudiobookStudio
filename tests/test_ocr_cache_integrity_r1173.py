from __future__ import annotations

import hashlib
from pathlib import Path

import fitz

from core.ocr import OCRService


def _make_pdf(path: Path, pages: int) -> None:
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        page.insert_text((72, 72), f"Page {index + 1} complete text")
    document.save(path)
    document.close()


def _manifest(text: str, pages: int, source: Path | None = None) -> dict:
    return {
        "schema": OCRService.CACHE_SCHEMA,
        "layout_schema": OCRService.LAYOUT_SCHEMA,
        "engine_preference": OCRService.engine_preference(),
        "complete": True,
        "source_page_count": pages,
        "pages": pages,
        "ocr_pages": pages,
        "embedded_pages": 0,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "page_word_counts": [4] * pages,
        "source_sha256": (
            hashlib.sha256(source.read_bytes()).hexdigest() if source else ""
        ),
    }


def test_cache_rejects_three_page_text_for_ten_page_pdf(tmp_path):
    source = tmp_path / "book.pdf"
    _make_pdf(source, 10)
    text = "one two three four\f" * 2 + "one two three four"
    valid, reasons = OCRService._validate_cached_payload(
        source, tmp_path, _manifest(text, 3, source), text
    )
    assert not valid
    assert any("10" in reason and "3" in reason for reason in reasons)


def test_cache_rejects_missing_complete_marker(tmp_path):
    source = tmp_path / "book.pdf"
    _make_pdf(source, 2)
    text = "one two three four\ffive six seven eight"
    manifest = _manifest(text, 2, source)
    manifest["complete"] = False
    valid, reasons = OCRService._validate_cached_payload(
        source, tmp_path, manifest, text
    )
    assert not valid
    assert any("not marked complete" in reason for reason in reasons)


def test_cache_rejects_text_hash_mismatch(tmp_path):
    source = tmp_path / "book.pdf"
    _make_pdf(source, 2)
    text = "one two three four\ffive six seven eight"
    manifest = _manifest(text, 2, source)
    manifest["text_sha256"] = "0" * 64
    valid, reasons = OCRService._validate_cached_payload(
        source, tmp_path, manifest, text
    )
    assert not valid
    assert any("hash" in reason for reason in reasons)


def test_complete_cache_payload_passes(tmp_path):
    source = tmp_path / "book.pdf"
    _make_pdf(source, 3)
    text = "one two three four\ffive six seven eight\fnine ten eleven twelve"
    valid, reasons = OCRService._validate_cached_payload(
        source, tmp_path, _manifest(text, 3, source), text
    )
    assert valid
    assert reasons == []


def test_cache_schema_was_incremented():
    assert OCRService.CACHE_SCHEMA >= 5
