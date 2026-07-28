from __future__ import annotations

from typing import Any

from core.chunker import split_into_chunks


def build_narration_plan(
    sections: list[dict[str, Any]],
    target_size: int = 900,
    min_size: int = 500,
    max_size: int = 1400,
) -> tuple[list[str], list[dict[str, Any]], str]:
    """Build chunks without allowing one chunk to cross chapter boundaries."""

    chunks: list[str] = []
    chapter_map: list[dict[str, Any]] = []
    narration_blocks: list[str] = []

    for order, section in enumerate(sections):
        text = str(section.get("text", "") or "").strip()
        if not text:
            continue

        chapter_chunks = split_into_chunks(
            text,
            target_size=target_size,
            min_size=min_size,
            max_size=max_size,
        )
        if not chapter_chunks:
            continue

        start_chunk = len(chunks) + 1
        chunks.extend(chapter_chunks)
        end_chunk = len(chunks)
        narration_blocks.append(text)

        chapter_map.append(
            {
                "index": int(section.get("index", order)),
                "order": len(chapter_map),
                "title": str(section.get("title", f"Chapter {order + 1}")),
                "source_title": str(section.get("source_title", section.get("title", ""))),
                "start_chunk": start_chunk,
                "end_chunk": end_chunk,
                "chunk_count": end_chunk - start_chunk + 1,
                "word_count": len(text.split()),
                "character_count": len(text),
                "included": True,
            }
        )

    return chunks, chapter_map, "\n\n".join(narration_blocks).strip()
