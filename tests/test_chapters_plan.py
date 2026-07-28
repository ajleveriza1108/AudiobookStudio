from core.chapters import apply_chapter_plan, detect_chapters
from core.narration_plan import build_narration_plan


def test_chapter_plan_can_rename_reorder_and_exclude():
    text = (
        "Chapter One\nFirst chapter words.\n\n"
        "Chapter Two\nSecond chapter words.\n\n"
        "Chapter Three\nThird chapter words."
    )
    detected = detect_chapters(text)
    assert [item["title"] for item in detected] == ["Chapter One", "Chapter Two", "Chapter Three"]

    sections = apply_chapter_plan(
        text,
        [
            {"index": 2, "title": "The Ending", "included": True},
            {"index": 0, "title": "The Beginning", "included": True},
            {"index": 1, "title": "Chapter Two", "included": False},
        ],
    )
    assert [item["title"] for item in sections] == ["The Ending", "The Beginning"]

    chunks, chapter_map, narration = build_narration_plan(
        sections,
        target_size=100,
        min_size=1,
        max_size=180,
    )
    assert len(chunks) == 2
    assert chapter_map[0]["start_chunk"] == 1
    assert chapter_map[0]["end_chunk"] == 1
    assert chapter_map[1]["start_chunk"] == 2
    assert "Second chapter" not in narration


def test_book_without_headings_becomes_one_full_book_section():
    text = "This scanned memoir has paragraphs but no printed chapter headings. " * 30
    detected = detect_chapters(text)
    assert len(detected) == 1
    assert detected[0]["title"] == "Full Book"
    assert detected[0]["included"] is True
    assert detected[0]["word_count"] > 0
