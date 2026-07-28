import json
from pathlib import Path
import sys
from types import ModuleType
import wave

if "ebooklib" not in sys.modules:
    ebooklib = ModuleType("ebooklib")
    ebooklib.ITEM_DOCUMENT = 9
    epub = ModuleType("ebooklib.epub")
    epub.read_epub = lambda *_: None
    ebooklib.epub = epub
    sys.modules["ebooklib"] = ebooklib
    sys.modules["ebooklib.epub"] = epub

from core.project import AudiobookProject


class FakeEngine:
    def speak(self, text, output_file, voice, speed, pitch):
        path = Path(output_file)
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24000)
            audio.writeframes(b"\x10\x00" * 7000)
        return str(path)


class FakeLibrary:
    def add(self, *_):
        return None

    def update_progress(self, *_):
        return None


class FakeLogger:
    def success(self, *_):
        return None


def test_project_uses_chapter_plan_and_creates_reports(monkeypatch, tmp_path):
    source = tmp_path / "book.pdf"
    source.write_bytes(b"placeholder")
    raw = "Chapter One\nFirst section.\n\nChapter Two\nSecond section."

    monkeypatch.setattr("core.project.extract_book_text", lambda *_, **__: raw)
    monkeypatch.setattr(
        "core.project.parse_book",
        lambda *_: {"title": "Test Book", "author": "Test Author", "pages": 2, "language": "en", "type": "PDF"},
    )
    monkeypatch.setattr("core.project.CoverExtractor.extract", lambda *_: None)
    monkeypatch.setattr("core.generator.EngineService.load", lambda *_: FakeEngine())

    project = AudiobookProject()
    project.library = FakeLibrary()
    project.logger = FakeLogger()
    output = tmp_path / "Output"
    result = project.build(
        book=source,
        output_folder=output,
        voice="af_heart",
        speed=1.0,
        pitch=0,
        chapter_plan=[
            {"index": 0, "title": "Opening", "included": True},
            {"index": 1, "title": "Second", "included": False},
        ],
        export_wav=True,
    )

    folder = output / "book"
    assert result
    assert (folder / "audiobook.wav").is_file()
    assert (folder / "Audio Quality Report.txt").is_file()
    assert (folder / "Book Preparation Report.txt").is_file()
    assert "Second section" not in (folder / "narration_text.txt").read_text(encoding="utf-8")
    chapters = json.loads((folder / "chapters.json").read_text(encoding="utf-8"))
    assert [item["title"] for item in chapters] == ["Opening"]
