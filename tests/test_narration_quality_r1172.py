from pathlib import Path

from core.narration_plan import build_narration_plan


def test_narration_plan_keeps_exact_approved_text():
    sections = [
        {
            "index": 0,
            "title": "Timeline",
            "source_title": "Timeline",
            "text": "January\nFirst event.\nFebruary\nSecond event.",
        },
        {
            "index": 1,
            "title": "News",
            "source_title": "News",
            "text": "A separate chapter sentence.",
        },
    ]
    chunks, chapters, narration = build_narration_plan(
        sections, target_size=100, min_size=1, max_size=160
    )
    assert chunks
    assert len(chapters) == 2
    assert chapters[0]["end_chunk"] < chapters[1]["start_chunk"]
    assert narration == (
        "January\nFirst event.\nFebruary\nSecond event."
        "\n\nA separate chapter sentence."
    )
    assert sections[0]["text"] in chunks[0]


def test_stable_chunker_generator_and_merger_match_r116_contract():
    root = Path(__file__).resolve().parents[1]
    plan = (root / "core" / "narration_plan.py").read_text(encoding="utf-8")
    assert "prepare_narration_text" not in plan
    assert 'text = str(section.get("text", "") or "").strip()' in plan

    for name in ("chunker.py", "generator.py", "merger.py"):
        source = (root / "core" / name).read_text(encoding="utf-8").casefold()
        assert "natural_pacing" not in source
        assert "natural paragraph pacing" not in source


def test_version_contract_preserves_r1173_or_newer():
    from core import version

    assert version.BUILD >= 173
    assert "R1.17." in version.VERSION


def test_isolated_update_payload_dependency_contract():
    from core.chunker import split_into_chunks

    assert split_into_chunks("One sentence.") == ["One sentence."]
