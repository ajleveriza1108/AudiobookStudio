import wave
from pathlib import Path

import pytest

from core.merger import AudioMerger


def write_wav(path: Path, frames: int):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x01\x00" * frames)


def test_merger_streams_chunks_in_order(tmp_path):
    write_wav(tmp_path / "chunk_00001.wav", 5000)
    write_wav(tmp_path / "chunk_00002.wav", 7000)

    output = tmp_path / "audiobook.wav"
    result = AudioMerger().merge(
        tmp_path,
        output,
        export_wav=True,
        expected_total=2,
    )

    assert result
    with wave.open(str(output), "rb") as merged:
        assert merged.getnframes() == 12000
        assert merged.getframerate() == 24000


def test_merger_rejects_unexpected_chunk_count(tmp_path):
    write_wav(tmp_path / "chunk_00001.wav", 5000)

    with pytest.raises(RuntimeError, match="Expected 2"):
        AudioMerger().merge(
            tmp_path,
            tmp_path / "audiobook.wav",
            expected_total=2,
        )


def test_m4b_export_receives_chapters_and_metadata(monkeypatch, tmp_path):
    write_wav(tmp_path / "chunk_00001.wav", 5000)
    write_wav(tmp_path / "chunk_00002.wav", 7000)
    calls = []

    def fake_run(arguments, timeout=None):
        calls.append(list(arguments))
        Path(arguments[-1]).write_bytes(b"m4b")
        return object()

    monkeypatch.setattr("core.merger.FFmpeg.run", fake_run)
    output = tmp_path / "audiobook.wav"
    result = AudioMerger().merge(
        tmp_path,
        output,
        export_wav=True,
        export_m4b=True,
        metadata={"title": "Book", "author": "Author", "narrator": "Narrator"},
        chapter_map=[
            {"title": "One", "start_chunk": 1, "end_chunk": 1},
            {"title": "Two", "start_chunk": 2, "end_chunk": 2},
        ],
    )

    assert result
    assert (tmp_path / "audiobook.m4b").is_file()
    assert calls
    assert "-map_chapters" in calls[0]
    assert not (tmp_path / "audiobook.ffmetadata.txt").exists()


def test_merger_ignores_nonstandard_chunk_named_wav(tmp_path):
    write_wav(tmp_path / "chunk_00001.wav", 5000)
    write_wav(tmp_path / "chunk_backup.wav", 9000)
    output = tmp_path / "audiobook.wav"
    assert AudioMerger().merge(tmp_path, output, expected_total=1)
    with wave.open(str(output), "rb") as merged:
        assert merged.getnframes() == 5000
