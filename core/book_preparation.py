from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any

from core.chapters import detect_chapters


_FRONT_MATTER = {
    "copyright",
    "title page",
    "dedication",
    "acknowledgments",
    "acknowledgements",
    "preface",
    "foreword",
    "contents",
    "table of contents",
}
_BACK_MATTER = {"index", "references", "bibliography", "notes", "glossary"}


def _issue(code: str, severity: str, title: str, detail: str, count: int = 1) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "title": title,
        "detail": detail,
        "count": int(count),
    }


def analyze_book_text(
    raw_text: str,
    cleaned_text: str,
    source: str | Path | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw = str(raw_text or "")
    cleaned = str(cleaned_text or "")
    pages = raw.split("\f") if "\f" in raw else [raw]
    paragraphs = [part.strip() for part in cleaned.split("\n\n") if part.strip()]
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    chapters = detect_chapters(cleaned)
    issues: list[dict[str, Any]] = []
    diagnostics = dict(diagnostics or {})

    blank_pages = sum(1 for page in pages if len(page.strip()) < 20)
    very_short_pages = sum(1 for page in pages if 0 < len(page.strip()) < 120)
    long_paragraphs = sum(1 for paragraph in paragraphs if len(paragraph) > 2500)
    urls = len(re.findall(r"\b(?:https?://|www\.)\S+", cleaned, re.IGNORECASE))
    emails = len(re.findall(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", cleaned))
    footnote_marks = len(re.findall(r"(?<!\w)\[(?:\d+|[a-z])\](?!\w)", raw, re.IGNORECASE))
    replacement_chars = cleaned.count("�")
    repeated_short_lines = Counter(line.casefold() for line in lines if len(line) <= 100)
    repeated_candidates = sum(1 for count in repeated_short_lines.values() if count >= 4)

    lower_paragraphs = {paragraph.casefold().strip(" .:") for paragraph in paragraphs[:20]}
    front_matter = sorted(lower_paragraphs.intersection(_FRONT_MATTER))
    lower_tail = {paragraph.casefold().strip(" .:") for paragraph in paragraphs[-30:]}
    back_matter = sorted(lower_tail.intersection(_BACK_MATTER))


    structured_pages = int(diagnostics.get("structured_pages") or 0)
    timeline_pages = int(diagnostics.get("timeline_pages") or 0)
    multi_column_pages = int(diagnostics.get("multi_column_pages") or 0)
    low_confidence_pages = int(diagnostics.get("low_confidence_pages") or 0)
    if structured_pages:
        modes: list[str] = []
        if timeline_pages:
            modes.append(f"{timeline_pages} timeline page(s)")
        if multi_column_pages:
            modes.append(f"{multi_column_pages} multi-column page(s)")
        detail = ", ".join(modes) or f"{structured_pages} structured page(s)"
        issues.append(
            _issue(
                "structured_ocr",
                "notice",
                "Layout-aware OCR reading order applied",
                "Audiobook Studio preserved OCR coordinates and ordered independent "
                f"regions instead of flattening each row: {detail}.",
                structured_pages,
            )
        )
    if low_confidence_pages:
        issues.append(
            _issue(
                "ocr_reading_order_review",
                "warning",
                "Some OCR pages need reading-order review",
                "Open the Cleaned Text tab and verify pages with uncertain or missing "
                "layout coordinates before creating a long audiobook.",
                low_confidence_pages,
            )
        )

    if blank_pages:
        issues.append(
            _issue(
                "blank_pages",
                "notice",
                "Blank or image-only pages found",
                "These pages may be intentional, but scanned books may require OCR before narration.",
                blank_pages,
            )
        )
    if very_short_pages >= 3:
        issues.append(
            _issue(
                "short_pages",
                "notice",
                "Several pages contain very little text",
                "Review the cleaned text for decorative, scanned, or incorrectly ordered pages.",
                very_short_pages,
            )
        )
    if long_paragraphs:
        issues.append(
            _issue(
                "long_paragraphs",
                "warning",
                "Very long paragraphs need review",
                "Long unbroken paragraphs can indicate damaged PDF layout or missing paragraph breaks.",
                long_paragraphs,
            )
        )
    if urls or emails:
        issues.append(
            _issue(
                "web_addresses",
                "notice",
                "Web or email addresses are present",
                "Consider pronunciation rules so addresses are spoken naturally.",
                urls + emails,
            )
        )
    if footnote_marks:
        issues.append(
            _issue(
                "footnotes",
                "notice",
                "Possible footnote markers are present",
                "Listen to a preview or remove unwanted footnote references before full generation.",
                footnote_marks,
            )
        )
    if replacement_chars:
        issues.append(
            _issue(
                "encoding",
                "warning",
                "Unreadable replacement characters were found",
                "The source may contain damaged or unsupported text encoding.",
                replacement_chars,
            )
        )
    if repeated_candidates:
        issues.append(
            _issue(
                "repeated_lines",
                "notice",
                "Repeated short lines were detected",
                "Audiobook Studio removes likely margin text, but the cleaned preview should still be checked.",
                repeated_candidates,
            )
        )
    if front_matter:
        issues.append(
            _issue(
                "front_matter",
                "notice",
                "Front matter was detected",
                "Review whether all opening material should be narrated: " + ", ".join(front_matter),
                len(front_matter),
            )
        )
    if back_matter:
        issues.append(
            _issue(
                "back_matter",
                "notice",
                "Back matter was detected",
                "Review whether reference material should be narrated: " + ", ".join(back_matter),
                len(back_matter),
            )
        )
    if len(chapters) <= 1 and len(cleaned.split()) > 5000:
        issues.append(
            _issue(
                "chapters",
                "warning",
                "No clear chapter headings were found",
                "Use the chapter review before creating an M4B audiobook.",
            )
        )

    words = len(cleaned.split())
    estimated_minutes = round(words / 155, 1) if words else 0.0
    source_path = str(Path(source).expanduser().resolve()) if source else ""

    return {
        "schema": 1,
        "source": source_path,
        "summary": {
            "pages": len(pages),
            "words": words,
            "characters": len(cleaned),
            "paragraphs": len(paragraphs),
            "chapters": len(chapters),
            "estimated_minutes": estimated_minutes,
            "raw_characters": len(raw),
            "removed_characters": max(0, len(raw) - len(cleaned)),
            "structured_ocr_pages": structured_pages,
            "timeline_pages": timeline_pages,
            "multi_column_pages": multi_column_pages,
            "low_confidence_ocr_pages": low_confidence_pages,
        },
        "issues": issues,
        "ready": not any(item["severity"] == "warning" for item in issues),
    }


def format_preparation_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "BOOK PREPARATION REPORT",
        "=" * 70,
        f"Words: {int(summary.get('words', 0)):,}",
        f"Paragraphs: {int(summary.get('paragraphs', 0)):,}",
        f"Detected chapters: {int(summary.get('chapters', 0)):,}",
        f"Estimated narration: {float(summary.get('estimated_minutes', 0.0)):.1f} minutes",
        "",
    ]

    issues = report.get("issues", [])
    if not issues:
        lines.append("No obvious preparation warnings were found. Review the cleaned text before generation.")
    else:
        lines.append("Review items:")
        for item in issues:
            severity = str(item.get("severity", "notice")).upper()
            count = int(item.get("count", 1))
            suffix = f" ({count})" if count > 1 else ""
            lines.append(f"- [{severity}] {item.get('title', 'Review item')}{suffix}")
            lines.append(f"  {item.get('detail', '')}")

    lines.extend(
        [
            "",
            "Before generating a long book, preview difficult names, numbers, abbreviations, and chapter boundaries.",
        ]
    )
    return "\n".join(lines)


def scanned_pdf_report(
    source: str | Path,
    *,
    pages: int,
    ocr_available: bool,
    ocr_backend: str = "",
) -> dict[str, Any]:
    """Create a truthful preparation report before OCR has been run."""

    if ocr_available:
        issues = [
            _issue(
                "scanned_pdf",
                "notice",
                "Scanned PDF detected",
                "This book contains page images instead of embedded text. "
                "Offline OCR will read the pages when generation starts. "
                "The recognized text will be cached for future use.",
                max(1, int(pages)),
            )
        ]
        ready = True
    else:
        issues = [
            _issue(
                "ocr_unavailable",
                "warning",
                "Offline OCR is required",
                "Run install_dependencies.ps1 to install RapidOCR and ONNX Runtime, "
                "then reopen the book.",
            )
        ]
        ready = False

    return {
        "schema": 1,
        "source": str(Path(source).expanduser().resolve()),
        "summary": {
            "pages": max(0, int(pages)),
            "words": 0,
            "characters": 0,
            "paragraphs": 0,
            "chapters": 1,
            "estimated_minutes": 0.0,
            "raw_characters": 0,
            "removed_characters": 0,
        },
        "issues": issues,
        "ready": ready,
        "scanned_pdf": True,
        "ocr_available": bool(ocr_available),
        "ocr_backend": str(ocr_backend or ""),
    }
