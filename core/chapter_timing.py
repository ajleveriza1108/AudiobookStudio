from __future__ import annotations

from pathlib import Path
import wave
from typing import Any

from core.chunk_validator import ChunkValidator


def wav_duration_ms(path: str | Path) -> int:
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        if rate <= 0:
            return 0
        return int(round((audio.getnframes() / rate) * 1000))


def build_chapter_timings(
    folder: str | Path,
    chapter_map: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    root = Path(folder)
    wav_files = ChunkValidator.ordered(root)
    durations = {index: wav_duration_ms(path) for index, path in enumerate(wav_files, start=1)}

    cumulative: dict[int, int] = {1: 0}
    running = 0
    for index in range(1, len(wav_files) + 1):
        cumulative[index] = running
        running += durations.get(index, 0)
    cumulative[len(wav_files) + 1] = running

    result: list[dict[str, Any]] = []
    for order, chapter in enumerate(chapter_map or []):
        start_chunk = max(1, int(chapter.get("start_chunk", 1)))
        end_chunk = max(start_chunk, int(chapter.get("end_chunk", start_chunk)))
        start_ms = cumulative.get(start_chunk, 0)
        end_ms = cumulative.get(end_chunk + 1, running)
        if end_ms <= start_ms:
            continue
        result.append(
            {
                "order": order,
                "title": str(chapter.get("title", f"Chapter {order + 1}")),
                "start_ms": start_ms,
                "end_ms": end_ms,
                "start_chunk": start_chunk,
                "end_chunk": end_chunk,
            }
        )

    if not result and running > 0:
        result.append(
            {
                "order": 0,
                "title": "Beginning",
                "start_ms": 0,
                "end_ms": running,
                "start_chunk": 1,
                "end_chunk": len(wav_files),
            }
        )
    return result


def escape_ffmetadata(value: Any) -> str:
    text = str(value or "")
    return text.replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\n", " ")


def write_ffmetadata(
    path: str | Path,
    metadata: dict[str, Any],
    chapters: list[dict[str, Any]],
) -> Path:
    destination = Path(path)
    lines = [";FFMETADATA1"]
    mapping = {
        "title": metadata.get("title"),
        "artist": metadata.get("author"),
        "album": metadata.get("title"),
        "composer": metadata.get("narrator"),
        "genre": metadata.get("genre", "Audiobook"),
        "comment": metadata.get("description"),
        "date": metadata.get("year"),
    }
    for key, value in mapping.items():
        if value not in (None, "", "Unknown"):
            lines.append(f"{key}={escape_ffmetadata(value)}")

    for chapter in chapters:
        lines.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={int(chapter['start_ms'])}",
                f"END={int(chapter['end_ms'])}",
                f"title={escape_ffmetadata(chapter['title'])}",
            ]
        )

    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
