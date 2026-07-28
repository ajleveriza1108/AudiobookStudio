from __future__ import annotations

from pathlib import Path

import fitz
import pytest

import sys
from types import ModuleType

if "ebooklib" not in sys.modules:
    ebooklib = ModuleType("ebooklib")
    ebooklib.ITEM_DOCUMENT = 9
    epub = ModuleType("ebooklib.epub")
    epub.read_epub = lambda *_: None
    ebooklib.epub = epub
    sys.modules["ebooklib"] = ebooklib
    sys.modules["ebooklib.epub"] = epub

from core.ocr import OCRAvailability, OCRService
from core.parser import ScannedPDFError, extract_book_text


def _image_only_pdf(path: Path) -> None:
    source = fitz.open()
    page = source.new_page(width=600, height=800)
    page.insert_text((72, 150), "SCANNED TEST PAGE", fontsize=30)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = pixmap.tobytes("png")
    source.close()

    document = fitz.open()
    target = document.new_page(width=600, height=800)
    target.insert_image(target.rect, stream=image)
    document.save(path)
    document.close()


def test_scanned_pdf_requires_ocr_then_reuses_cache(monkeypatch, tmp_path):
    source = tmp_path / "scan.pdf"
    _image_only_pdf(source)

    with pytest.raises(ScannedPDFError):
        extract_book_text(source)

    monkeypatch.setattr(
        OCRService,
        "availability",
        classmethod(lambda cls: OCRAvailability(True, "Fake OCR", "ready")),
    )
    monkeypatch.setattr(
        OCRService,
        "_recognize_page",
        classmethod(lambda cls, pixmap, backend, language: "A scanned page with readable words."),
    )

    diagnostics = {}
    text = extract_book_text(source, ocr_if_needed=True, diagnostics=diagnostics)
    assert "scanned page" in text.lower()
    assert diagnostics["ocr_used"] is True
    assert diagnostics["ocr_backend"] == "Fake OCR"

    cached = OCRService.cached_text(source)
    assert cached is not None
    assert cached.cache_hit is True

    # Preview-style extraction does not need to rerun OCR after the cache exists.
    second_diagnostics = {}
    second = extract_book_text(source, diagnostics=second_diagnostics)
    assert second == text
    assert second_diagnostics["ocr_cache_hit"] is True


def test_mixed_pdf_ocr_keeps_embedded_pages(monkeypatch, tmp_path):
    source = tmp_path / "mixed.pdf"
    document = fitz.open()
    page1 = document.new_page()
    page1.insert_text((72, 72), "This is embedded selectable text on page one.")
    page2 = document.new_page()
    # A tiny image makes page two image-only for the extraction path.
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), 0)
    pix.clear_with(255)
    page2.insert_image(page2.rect, pixmap=pix)
    document.save(source)
    document.close()

    monkeypatch.setattr(
        OCRService,
        "availability",
        classmethod(lambda cls: OCRAvailability(True, "Fake OCR", "ready")),
    )
    monkeypatch.setattr(
        OCRService,
        "_recognize_page",
        classmethod(lambda cls, pixmap, backend, language: "Recognized image page two."),
    )

    diagnostics = {}
    text = extract_book_text(source, ocr_if_needed=True, diagnostics=diagnostics)
    assert "embedded selectable text" in text
    assert "Recognized image page two" in text
    assert diagnostics["ocr_used"] is True
