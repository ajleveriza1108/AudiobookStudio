from __future__ import annotations

import re


DEFAULT_TARGET = 900
DEFAULT_MIN = 500
DEFAULT_MAX = 1400

ABBREVIATIONS = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.",
    "vs.", "etc.", "e.g.", "i.e.", "a.m.", "p.m.", "no.", "fig.",
    "rev.", "hon.", "gen.", "capt.", "lt.", "col.", "mt.", "jan.",
    "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.",
    "oct.", "nov.", "dec.",
}


def normalize(text):
    value = str(text or "").replace("\r", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _token_before(text: str, index: int) -> str:
    start = index
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    return text[start:index + 1].strip("\"'“”‘’()[]{}")


def _is_sentence_boundary(text: str, index: int) -> bool:
    character = text[index]
    if character not in ".!?":
        return False

    if character == ".":
        token = _token_before(text, index).casefold()
        if token in ABBREVIATIONS:
            return False
        if re.fullmatch(r"[a-z]\.", token, re.IGNORECASE):
            return False
        if index > 0 and index + 1 < len(text):
            if text[index - 1].isdigit() and text[index + 1].isdigit():
                return False
        if text[index:index + 3] == "...":
            return False

    cursor = index + 1
    while cursor < len(text) and text[cursor] in "\"'”’)]}":
        cursor += 1

    return cursor >= len(text) or text[cursor].isspace()


def split_sentences(text):
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if not value:
        return []

    sentences: list[str] = []
    start = 0
    index = 0

    while index < len(value):
        if _is_sentence_boundary(value, index):
            end = index + 1
            while end < len(value) and value[end] in "\"'”’)]}":
                end += 1
            sentence = value[start:end].strip()
            if sentence:
                sentences.append(sentence)
            while end < len(value) and value[end].isspace():
                end += 1
            start = end
            index = end
            continue
        index += 1

    tail = value[start:].strip()
    if tail:
        sentences.append(tail)

    return sentences


def _split_oversized(text: str, target_size: int, max_size: int) -> list[str]:
    pieces: list[str] = []
    current = ""

    clauses = re.split(r"(?<=[,;:—–])\s+", text)
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue

        candidate = f"{current} {clause}".strip()
        if current and len(candidate) > max_size:
            pieces.append(current)
            current = ""

        if len(clause) <= max_size:
            current = f"{current} {clause}".strip()
            continue

        words = clause.split()
        word_piece = ""
        for word in words:
            candidate = f"{word_piece} {word}".strip()
            if word_piece and len(candidate) > target_size:
                pieces.append(word_piece)
                word_piece = word
            else:
                word_piece = candidate
        if word_piece:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(word_piece)

    if current:
        pieces.append(current)

    return pieces


def split_into_chunks(
    text,
    target_size=DEFAULT_TARGET,
    min_size=DEFAULT_MIN,
    max_size=DEFAULT_MAX,
):
    value = normalize(text)
    if not value:
        return []

    target_size = max(100, int(target_size))
    min_size = max(1, min(int(min_size), target_size))
    max_size = max(target_size, int(max_size))

    paragraphs = [part.strip() for part in value.split("\n\n") if part.strip()]
    units: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= max_size:
            units.append(paragraph)
            continue

        for sentence in split_sentences(paragraph):
            if len(sentence) <= max_size:
                units.append(sentence)
            else:
                units.extend(_split_oversized(sentence, target_size, max_size))

    chunks: list[str] = []
    current = ""

    for unit in units:
        separator = "\n\n" if current else ""
        candidate = f"{current}{separator}{unit}"

        if current and len(candidate) > max_size:
            chunks.append(current.strip())
            current = unit
        else:
            current = candidate

        if len(current) >= target_size:
            chunks.append(current.strip())
            current = ""

    if current.strip():
        if chunks and len(current) < min_size and len(chunks[-1]) + 2 + len(current) <= max_size:
            chunks[-1] = f"{chunks[-1]}\n\n{current.strip()}"
        else:
            chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk]


def estimate_chunks(text, target_size=DEFAULT_TARGET):
    value = str(text or "")
    return max(1, (len(value) + target_size - 1) // target_size)


def average_chunk_size(chunks):
    if not chunks:
        return 0
    return sum(len(chunk) for chunk in chunks) // len(chunks)


def statistics(chunks):
    if not chunks:
        return {"chunks": 0, "largest": 0, "smallest": 0, "average": 0}

    sizes = [len(chunk) for chunk in chunks]
    return {
        "chunks": len(chunks),
        "largest": max(sizes),
        "smallest": min(sizes),
        "average": sum(sizes) // len(sizes),
    }
