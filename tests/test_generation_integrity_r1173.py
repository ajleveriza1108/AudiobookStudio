from __future__ import annotations

from pathlib import Path
import wave

import pytest

from core.generation_integrity import (
    GenerationIntegrityError,
    build_pre_generation_report,
    promote_candidate,
    require_merged_audio_integrity,
    validate_chunk_set,
)


def _page(words: int, label: str) -> str:
    return " ".join([label] + [f"word{i}" for i in range(words - 1)])


def _write_wav(path: Path, frames: int, sample_rate: int = 24000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x01\x00" * frames)


def test_three_of_ten_page_narration_is_blocked():
    pages = [_page(100, f"page{i}") for i in range(1, 11)]
    raw = "\f".join(pages)
    cleaned = "\n\n".join(pages)
    narration = "\n\n".join(pages[:3])
    chunks = [narration[index:index + 900] for index in range(0, len(narration), 900)]
    report = build_pre_generation_report(
        source="book.pdf",
        raw_text=raw,
        cleaned_text=cleaned,
        narration_text=narration,
        chunks=chunks,
        chapters=[{"word_count": len(narration.split())}],
        chapter_plan=None,
        metadata={"pages": 10},
        diagnostics={
            "pages": 10,
            "ocr_used": True,
            "ocr_pages": 10,
            "readable_pages": 0,
        },
    )
    assert report["status"] == "blocked"
    assert any("retains only" in item for item in report["failures"])


def test_pdf_page_count_mismatch_is_blocked():
    raw = "\f".join(_page(50, f"page{i}") for i in range(1, 4))
    report = build_pre_generation_report(
        source="book.pdf",
        raw_text=raw,
        cleaned_text=raw.replace("\f", "\n\n"),
        narration_text=raw.replace("\f", "\n\n"),
        chunks=[raw.replace("\f", "\n\n")],
        chapters=[{"word_count": 150}],
        chapter_plan=None,
        metadata={"pages": 10},
        diagnostics={"pages": 3, "ocr_used": True, "ocr_pages": 3, "readable_pages": 0},
    )
    assert report["status"] == "blocked"
    assert any("10 pages" in item and "3" in item for item in report["failures"])


def test_complete_ten_page_plan_passes():
    pages = [_page(80, f"page{i}") for i in range(1, 11)]
    raw = "\f".join(pages)
    narration = "\n\n".join(pages)
    chunks = [narration[index:index + 900] for index in range(0, len(narration), 900)]
    report = build_pre_generation_report(
        source="book.pdf",
        raw_text=raw,
        cleaned_text=narration,
        narration_text=narration,
        chunks=chunks,
        chapters=[{"word_count": len(narration.split())}],
        chapter_plan=None,
        metadata={"pages": 10},
        diagnostics={
            "pages": 10,
            "ocr_used": True,
            "ocr_pages": 10,
            "readable_pages": 0,
        },
    )
    assert report["status"] == "passed"
    assert not report["failures"]


def test_chunk_validation_rejects_missing_middle_number(tmp_path):
    _write_wav(tmp_path / "chunk_00001.wav", 24000)
    _write_wav(tmp_path / "chunk_00003.wav", 24000)
    report = validate_chunk_set(tmp_path, expected_total=2)
    assert report["status"] == "blocked"
    assert report["missing"] == [2]
    assert report["unexpected"] == [3]


def test_assembled_wav_must_equal_all_chunk_frames(tmp_path):
    _write_wav(tmp_path / "chunk_00001.wav", 24000)
    _write_wav(tmp_path / "chunk_00002.wav", 24000)
    candidate = tmp_path / "audiobook.candidate.wav"
    _write_wav(candidate, 24000)

    with pytest.raises(GenerationIntegrityError):
        require_merged_audio_integrity(
            tmp_path,
            candidate=candidate,
            chunk_folder=tmp_path,
            expected_total=2,
            narration_words=300,
            speed=1.0,
            base_report={"failures": []},
        )
    assert not candidate.exists()


def test_candidate_promotion_preserves_existing_audio(tmp_path):
    final = tmp_path / "audiobook.wav"
    candidate = tmp_path / "audiobook.candidate.wav"
    _write_wav(final, 24000)
    old_size = final.stat().st_size
    _write_wav(candidate, 48000)

    previous = promote_candidate(candidate, final)
    assert previous is not None and previous.is_file()
    assert previous.stat().st_size == old_size
    with wave.open(str(final), "rb") as wav:
        assert wav.getnframes() == 48000
    assert not candidate.exists()


def test_project_assembles_candidate_before_replacing_final():
    source = (
        Path(__file__).resolve().parents[1] / "core" / "project.py"
    ).read_text(encoding="utf-8")
    assert 'candidate_wav = project / "audiobook.candidate.wav"' in source
    assert "require_merged_audio_integrity(" in source
    assert source.index("require_merged_audio_integrity(") < source.index(
        "promote_candidate(candidate_wav, final_wav)"
    )


def test_r1173_removes_regressed_natural_pacing_pipeline():
    root = Path(__file__).resolve().parents[1]
    targets = [
        root / "app.py",
        root / "controllers" / "app_controller.py",
        root / "core" / "project.py",
        root / "core" / "job.py",
        root / "core" / "batch.py",
        root / "core" / "generator.py",
        root / "core" / "chunker.py",
        root / "core" / "merger.py",
        root / "core" / "narration_plan.py",
        root / "workers" / "generator_worker.py",
        root / "ui" / "settings_narrator.py",
    ]
    for path in targets:
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8").casefold()
        assert "natural_pacing" not in source, path
        assert "natural paragraph pacing" not in source, path
        assert "prepare_narration_text" not in source, path
