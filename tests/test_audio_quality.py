import wave

from core.audio_quality import AudioQualityAnalyzer


def test_audio_quality_report_is_created(tmp_path):
    wav = tmp_path / "audiobook.wav"
    with wave.open(str(wav), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x10\x00" * 24000)

    report = AudioQualityAnalyzer.analyze(wav)
    assert report["valid"]
    assert report["duration_seconds"] == 1.0
    json_path, text_path = AudioQualityAnalyzer.save(report, tmp_path)
    assert json_path.is_file()
    assert "AUDIOBOOK STUDIO" in text_path.read_text(encoding="utf-8")
