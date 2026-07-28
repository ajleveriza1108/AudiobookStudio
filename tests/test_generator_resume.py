import wave
from pathlib import Path

from core.generator import AudiobookGenerator
from core.resume import ResumeManager


class FakeEngine:
    def __init__(self):
        self.calls = []

    def speak(self, text, output_file, voice, speed, pitch):
        self.calls.append((text, voice, speed, pitch))
        path = Path(output_file)
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24000)
            audio.writeframes(b"\x00\x00" * 7000)
        return str(path)


def test_generator_reuses_matching_chunks(monkeypatch, tmp_path):
    fake = FakeEngine()
    monkeypatch.setattr("core.generator.EngineService.load", lambda name: fake)

    chunks = ["First section.", "Second section."]
    manager = ResumeManager(tmp_path)
    generator = AudiobookGenerator()

    assert generator.generate(
        title="Book",
        chunks=chunks,
        output_folder=tmp_path,
        voice="af_heart",
        speed=1.0,
        pitch=0,
        resume_manager=manager,
        source_file=tmp_path / "book.pdf",
        text_hash="hash",
    )
    assert len(fake.calls) == 2

    second_fake = FakeEngine()
    monkeypatch.setattr("core.generator.EngineService.load", lambda name: second_fake)
    assert generator.generate(
        title="Book",
        chunks=chunks,
        output_folder=tmp_path,
        voice="af_heart",
        speed=1.0,
        pitch=0,
        resume_manager=ResumeManager(tmp_path),
        source_file=tmp_path / "book.pdf",
        text_hash="hash",
    )
    assert second_fake.calls == []
