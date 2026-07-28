from __future__ import annotations

import re
from typing import Any


_NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    "thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    "thirty|forty|fifty|sixty|seventy|eighty|ninety"
)

_CHAPTER_HEADING = re.compile(
    rf"^(?:chapter|book|part|section|volume)\s+"
    rf"(?:\d+|[ivxlcdm]+|{_NUMBER_WORDS})(?:\s*[:.\-–—]\s*.*|\s+.+)?$|"
    r"^(?:prologue|epilogue|introduction|preface|foreword|afterword|"
    r"acknowledg(?:e)?ments|appendix(?:\s+[a-z0-9ivxlcdm]+)?)\b.*$",
    re.IGNORECASE,
)

_STANDALONE_NUMBER = re.compile(
    r"^(?:\d{1,3}|[ivxlcdm]{1,12})[.)]?\s+(?:[A-Z][^.!?]{1,80})$"
)


def is_chapter_heading(line: str) -> bool:
    candidate = " ".join(str(line or "").strip().split())
    if not candidate or len(candidate) > 140:
        return False
    if _CHAPTER_HEADING.match(candidate):
        return True
    return bool(_STANDALONE_NUMBER.match(candidate))


def full_book_chapter(text: str = "", *, virtual: bool = False) -> dict[str, Any]:
    value = str(text or "")
    return {
        "index": 0,
        "title": "Full Book",
        "source_title": "Full Book",
        "position": 0,
        "end": len(value),
        "included": True,
        "word_count": len(value.split()),
        "character_count": len(value),
        "virtual": bool(virtual),
    }


def detect_chapters(text: str) -> list[dict[str, Any]]:
    value = str(text or "")
    chapters: list[dict[str, Any]] = []
    position = 0

    for line in value.splitlines(keepends=True):
        candidate = line.strip()
        if is_chapter_heading(candidate):
            chapters.append(
                {
                    "index": len(chapters),
                    "title": candidate,
                    "source_title": candidate,
                    "position": position,
                    "included": True,
                }
            )
        position += len(line)

    # A book does not need printed chapter headings to be narratable. Treat it
    # as one complete section instead of leaving the chapter table empty.
    if not chapters:
        return [full_book_chapter(value)]

    if chapters[0]["position"] > 0:
        chapters.insert(
            0,
            {
                "index": 0,
                "title": "Opening",
                "source_title": "Opening",
                "position": 0,
                "included": True,
            },
        )

    # Deduplicate headings that appear at the same character position.
    unique: list[dict[str, Any]] = []
    seen_positions: set[int] = set()
    for chapter in chapters:
        position = int(chapter["position"])
        if position in seen_positions:
            continue
        seen_positions.add(position)
        chapter["index"] = len(unique)
        unique.append(chapter)

    for index, chapter in enumerate(unique):
        end = unique[index + 1]["position"] if index + 1 < len(unique) else len(value)
        chapter["end"] = int(end)
        section_text = value[int(chapter["position"]):int(end)].strip()
        chapter["word_count"] = len(section_text.split())
        chapter["character_count"] = len(section_text)

    return unique


def chapter_sections(text: str) -> list[dict[str, Any]]:
    value = str(text or "")
    result: list[dict[str, Any]] = []
    for chapter in detect_chapters(value):
        start = int(chapter["position"])
        end = int(chapter["end"])
        section = dict(chapter)
        section["text"] = value[start:end].strip()
        result.append(section)
    return result


def split_by_chapters(text: str) -> list[str]:
    return [section["text"] for section in chapter_sections(text)]


def _normalized_plan(plan: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    normalized: dict[int, dict[str, Any]] = {}
    for position, item in enumerate(plan or []):
        try:
            index = int(item.get("index", position))
        except (TypeError, ValueError, AttributeError):
            index = position
        if isinstance(item, dict):
            normalized[index] = item
    return normalized


def apply_chapter_plan(
    text: str,
    plan: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return selected chapter sections with user titles and order applied.

    The function remains safe when an older caller supplies no plan. Unknown
    plan entries are ignored, while omitted detected chapters keep their
    original settings.
    """

    sections = chapter_sections(text)
    if not plan:
        return sections

    detected_by_index = {int(item["index"]): item for item in sections}
    requested = _normalized_plan(plan)
    ordered_indexes: list[int] = []

    for position, item in enumerate(plan):
        try:
            index = int(item.get("index", position))
        except (TypeError, ValueError, AttributeError):
            continue
        if index in detected_by_index and index not in ordered_indexes:
            ordered_indexes.append(index)

    for index in sorted(detected_by_index):
        if index not in ordered_indexes:
            ordered_indexes.append(index)

    selected: list[dict[str, Any]] = []
    for detected_index in ordered_indexes:
        source = dict(detected_by_index[detected_index])
        override = requested.get(detected_index, {})
        included = bool(override.get("included", source.get("included", True)))
        if not included:
            continue

        title = str(override.get("title", source["title"]) or source["title"]).strip()
        source["title"] = title or source["title"]
        source["included"] = True
        source["order"] = len(selected)
        selected.append(source)

    return selected
