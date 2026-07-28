import wave

from core.chapter_timing import build_chapter_timings, write_ffmetadata


def _wav(path, frames):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(1000)
        audio.writeframes(b"\x00\x00" * frames)


def test_chapter_timings_and_ffmetadata(tmp_path):
    _wav(tmp_path / "chunk_00001.wav", 1000)
    _wav(tmp_path / "chunk_00002.wav", 2000)
    timings = build_chapter_timings(
        tmp_path,
        [
            {"title": "One", "start_chunk": 1, "end_chunk": 1},
            {"title": "Two", "start_chunk": 2, "end_chunk": 2},
        ],
    )
    assert timings[0]["start_ms"] == 0
    assert timings[0]["end_ms"] == 1000
    assert timings[1]["start_ms"] == 1000
    assert timings[1]["end_ms"] == 3000

    metadata = write_ffmetadata(tmp_path / "chapters.txt", {"title": "Book", "author": "Author"}, timings)
    content = metadata.read_text(encoding="utf-8")
    assert "[CHAPTER]" in content
    assert "title=One" in content
    assert "artist=Author" in content
