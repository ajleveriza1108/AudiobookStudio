from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import fitz
from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub


SUPPORTED = [".pdf", ".epub"]


class BookParsingError(RuntimeError):
    """Raised when a supported book cannot provide usable text."""


class ScannedPDFError(BookParsingError):
    """Raised when a PDF contains images but no usable embedded text."""


def _metadata_value(value: Any, fallback: str = "Unknown") -> str:
    text = str(value or "").strip()
    return text or fallback


def parse_book(book):
    path = Path(book)
    suffix = path.suffix.lower()

    if not path.is_file():
        raise FileNotFoundError(f"Book file was not found: {path}")

    if suffix == ".pdf":
        return parse_pdf(path)

    if suffix == ".epub":
        return parse_epub(path)

    raise BookParsingError(f"Unsupported book format: {suffix or 'unknown'}")


def parse_pdf(book):
    path = Path(book)
    with fitz.open(path) as pdf:
        metadata = pdf.metadata or {}
        return {
            "title": _metadata_value(metadata.get("title"), path.stem),
            "author": _metadata_value(metadata.get("author")),
            "pages": pdf.page_count,
            "language": _metadata_value(metadata.get("language")),
            "type": "PDF",
        }


def _first_epub_metadata(epub_book, namespace: str, name: str, fallback: str) -> str:
    try:
        values = epub_book.get_metadata(namespace, name)
        if values:
            return _metadata_value(values[0][0], fallback)
    except (IndexError, TypeError, AttributeError):
        pass
    return fallback


def parse_epub(book):
    path = Path(book)
    epub_book = epub.read_epub(str(path))
    return {
        "title": _first_epub_metadata(epub_book, "DC", "title", path.stem),
        "author": _first_epub_metadata(epub_book, "DC", "creator", "Unknown"),
        "pages": "Unknown",
        "language": _first_epub_metadata(epub_book, "DC", "language", "Unknown"),
        "type": "EPUB",
    }


def _extract_pdf_pages(book: str | Path) -> list[str]:
    path = Path(book)
    pages: list[str] = []

    with fitz.open(path) as pdf:
        for page in pdf:
            try:
                text = page.get_text("text", sort=True) or ""
            except (RuntimeError, ValueError):
                text = ""
            pages.append(text.strip())
    return pages


def pdf_text_diagnostics(book: str | Path) -> dict[str, Any]:
    path = Path(book).expanduser().resolve()
    pages = _extract_pdf_pages(path)
    readable_pages = sum(1 for text in pages if len(text.strip()) >= 24)
    image_only_pages = len(pages) - readable_pages
    characters = sum(len(text) for text in pages)
    words = sum(len(text.split()) for text in pages)
    return {
        "pages": len(pages),
        "readable_pages": readable_pages,
        "image_only_pages": image_only_pages,
        "characters": characters,
        "words": words,
        "scanned": bool(pages) and readable_pages == 0,
        "mixed": readable_pages > 0 and image_only_pages > 0,
    }


def extract_book_text(
    book,
    *,
    ocr_if_needed: bool = False,
    progress_callback: Callable[[int, int, str], None] | None = None,
    cancel_callback: Callable[[], bool] | None = None,
    log_callback: Callable[[str], None] | None = None,
    diagnostics: dict[str, Any] | None = None,
):
    path = Path(book)
    suffix = path.suffix.lower()

    if not path.is_file():
        raise FileNotFoundError(f"Book file was not found: {path}")

    info = diagnostics if diagnostics is not None else {}

    if suffix == ".pdf":
        pages = _extract_pdf_pages(path)
        text = "\n\f\n".join(pages)
        readable_pages = sum(1 for page in pages if len(page.strip()) >= 24)
        image_only_pages = len(pages) - readable_pages
        info.update(
            {
                "source_mode": "embedded",
                "pages": len(pages),
                "readable_pages": readable_pages,
                "image_only_pages": image_only_pages,
                "ocr_used": False,
                "ocr_backend": "",
                "ocr_cache_hit": False,
                "structured_pages": 0,
                "timeline_pages": 0,
                "multi_column_pages": 0,
                "low_confidence_pages": 0,
                "layout_schema": 0,
                "correction_profile": "",
                "ocr_cache_folder": "",
            }
        )

        # Scanned books can be reopened immediately after a prior OCR pass,
        # even when this caller is only asking for preview text.
        if not text.strip():
            from core.ocr import OCRService

            cached = OCRService.cached_text(path)
            if cached is not None:
                info.update(
                    {
                        "source_mode": "ocr-cache",
                        "ocr_used": True,
                        "ocr_backend": cached.backend,
                        "ocr_cache_hit": True,
                        "ocr_pages": cached.ocr_pages,
                        "structured_pages": cached.structured_pages,
                        "timeline_pages": cached.timeline_pages,
                        "multi_column_pages": cached.multi_column_pages,
                        "low_confidence_pages": cached.low_confidence_pages,
                        "layout_schema": cached.layout_schema,
                        "correction_profile": cached.correction_profile,
                        "ocr_cache_folder": str(cached.cache_folder),
                    }
                )
                return cached.text

        # For generation, OCR completely scanned PDFs and the image-only pages
        # of mixed PDFs. Embedded pages are retained exactly as extracted.
        needs_ocr = image_only_pages > 0 and (
            readable_pages == 0 or image_only_pages >= max(1, len(pages) // 4)
        )
        if ocr_if_needed and needs_ocr:
            from core.ocr import OCRService

            result = OCRService.extract_pdf(
                path,
                embedded_pages=pages,
                progress_callback=progress_callback,
                cancel_callback=cancel_callback,
                log_callback=log_callback,
            )
            info.update(
                {
                    "source_mode": "ocr-cache" if result.cache_hit else "ocr",
                    "ocr_used": True,
                    "ocr_backend": result.backend,
                    "ocr_cache_hit": result.cache_hit,
                    "ocr_pages": result.ocr_pages,
                    "readable_pages": result.embedded_pages,
                    "image_only_pages": result.ocr_pages,
                    "structured_pages": result.structured_pages,
                    "timeline_pages": result.timeline_pages,
                    "multi_column_pages": result.multi_column_pages,
                    "low_confidence_pages": result.low_confidence_pages,
                    "layout_schema": result.layout_schema,
                    "correction_profile": result.correction_profile,
                    "ocr_cache_folder": str(result.cache_folder),
                }
            )
            text = result.text

        if not text.strip():
            raise ScannedPDFError(
                "This PDF contains scanned page images but no readable embedded text. "
                "Offline OCR is required before narration."
            )
    elif suffix == ".epub":
        text = extract_epub(path)
        info.update(
            {
                "source_mode": "embedded",
                "pages": 0,
                "readable_pages": 0,
                "image_only_pages": 0,
                "ocr_used": False,
                "ocr_backend": "",
                "ocr_cache_hit": False,
                "structured_pages": 0,
                "timeline_pages": 0,
                "multi_column_pages": 0,
                "low_confidence_pages": 0,
                "layout_schema": 0,
                "correction_profile": "",
                "ocr_cache_folder": "",
            }
        )
    else:
        raise BookParsingError(f"Unsupported book format: {suffix or 'unknown'}")

    if not text.strip():
        raise BookParsingError(
            "No readable text was found. This may be a scanned or image-only book."
        )

    return text


def extract_pdf(book):
    return "\n\f\n".join(_extract_pdf_pages(book))


def extract_epub(book):
    path = Path(book)
    epub_book = epub.read_epub(str(path))
    sections: list[str] = []

    for item in epub_book.get_items():
        if item.get_type() != ITEM_DOCUMENT:
            continue

        soup = BeautifulSoup(item.get_content(), "html.parser")
        for unwanted in soup(["script", "style", "noscript"]):
            unwanted.decompose()

        text = soup.get_text("\n", strip=True)
        if text:
            sections.append(text)

    return "\n\n".join(sections)


def extract_cover(book):
    path = Path(book)
    if path.suffix.lower() != ".epub":
        return None

    try:
        epub_book = epub.read_epub(str(path))
        for item in epub_book.get_items():
            name = item.get_name().lower()
            if "cover" in name and item.get_content():
                return item.get_content()
    except (OSError, ValueError, KeyError, AttributeError):
        return None

    return None


def page_count(book):
    path = Path(book)
    if path.suffix.lower() != ".pdf":
        return 0

    with fitz.open(path) as pdf:
        return pdf.page_count
