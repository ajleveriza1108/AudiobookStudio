from __future__ import annotations

from collections import Counter
import re


HEADER_PATTERNS = [
    r"^\s*\d+\s*$",
    r"^\s*page\s+\d+(?:\s+of\s+\d+)?\s*$",
    r"^\s*copyright(?:\s+©)?\b",
    r"^\s*isbn(?:-1[03])?\b",
    r"^\s*printed in\b",
    r"^\s*all rights reserved\b",
]

CHAPTER_PATTERN = re.compile(
    r"^(?:chapter|book|part)\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)\b|^(?:prologue|epilogue|introduction|preface|foreword|afterword)\b",
    re.IGNORECASE,
)


def _normalize_line(line: str) -> str:
    line = line.replace("\u00a0", " ").replace("\u200b", "")
    return re.sub(r"[ \t]+", " ", line).strip()


def _looks_like_page_noise(line: str) -> bool:
    lower = line.casefold()
    return any(re.match(pattern, lower) for pattern in HEADER_PATTERNS)


def _repeating_margin_lines(pages: list[list[str]]) -> set[str]:
    if len(pages) < 3:
        return set()

    candidates: Counter[str] = Counter()
    for lines in pages:
        nonempty = [line for line in lines if line]
        margin = nonempty[:3] + nonempty[-3:]
        for line in set(margin):
            if len(line) <= 120:
                candidates[line.casefold()] += 1

    threshold = max(3, int(len(pages) * 0.4))
    return {line for line, count in candidates.items() if count >= threshold}


def _looks_like_heading(line: str) -> bool:
    if not line or len(line) > 100:
        return False
    if CHAPTER_PATTERN.match(line):
        return True
    letters = [character for character in line if character.isalpha()]
    return bool(letters) and len(letters) >= 3 and line.upper() == line


def _should_start_new_paragraph(previous: str, current: str) -> bool:
    if not previous:
        return True
    if _looks_like_heading(previous) or _looks_like_heading(current):
        return True
    if current.startswith(("“", '"', "‘", "'", "—", "–")):
        return True
    if previous.endswith((".", "!", "?", ":", ";", "”", '"', "’")):
        return True
    return False


def clean_text(text):
    value = str(text or "")
    value = value.replace("\r", "")
    value = value.replace("\t", " ")
    value = value.replace("\x00", "")
    value = value.replace("\ufeff", "")

    # Repair words split by line wrapping while preserving real hyphenated words.
    value = re.sub(r"(?<=\w)-\n(?=[a-z])", "", value)

    raw_pages = value.split("\f")
    pages: list[list[str]] = []
    for page in raw_pages:
        lines = [_normalize_line(line) for line in page.splitlines()]
        pages.append(lines)

    repeated = _repeating_margin_lines(pages)
    blocks: list[str] = []

    for page_lines in pages:
        paragraph = ""

        for line in page_lines:
            if not line:
                if paragraph:
                    blocks.append(paragraph.strip())
                    paragraph = ""
                continue

            if line.casefold() in repeated or _looks_like_page_noise(line):
                continue

            # Remove numeric citation markers but retain meaningful bracketed text.
            line = re.sub(r"\[(?:\d+|\d+[–-]\d+)\]", "", line)
            line = re.sub(r"\(\s*[Pp]age\s+\d+\s*\)", "", line)
            line = _normalize_line(line)
            if not line:
                continue

            if _should_start_new_paragraph(paragraph, line):
                if paragraph:
                    blocks.append(paragraph.strip())
                paragraph = line
            else:
                paragraph = f"{paragraph} {line}".strip()

        if paragraph:
            blocks.append(paragraph.strip())

    cleaned: list[str] = []
    for block in blocks:
        block = re.sub(r"\s+", " ", block).strip()
        if block:
            cleaned.append(block)

    return "\n\n".join(cleaned).strip()


def preview(text, length=5000):
    return str(text or "")[:length]


def character_count(text):
    return len(str(text or ""))


def word_count(text):
    return len(str(text or "").split())
