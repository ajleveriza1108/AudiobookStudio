import wave
from pathlib import Path

from core.resume import ResumeManager


def write_wav(path: Path, frames: int = 6000):
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(24000)
        audio.writeframes(b"\x00\x00" * frames)


def test_resume_reuses_only_matching_valid_chunks(tmp_path):
    manager = ResumeManager(tmp_path)
    settings = {
        "engine": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
        "pitch": 0.0,
    }
    manager.begin(1, tmp_path / "book.pdf", settings, "book-hash")

    wav = tmp_path / "chunk_00001.wav"
    write_wav(wav)
    manager.mark_completed(1, 1, "Hello world.", settings, wav)

    assert manager.is_current(1, "Hello world.", settings, wav)
    assert not manager.is_current(1, "Changed text.", settings, wav)
    assert not manager.is_current(
        1,
        "Hello world.",
        {**settings, "voice": "am_adam"},
        wav,
    )


def test_resume_removes_old_tail_chunks(tmp_path):
    for index in range(1, 4):
        write_wav(tmp_path / f"chunk_{index:05d}.wav")

    manager = ResumeManager(tmp_path)
    manager.begin(
        2,
        tmp_path / "book.pdf",
        {"engine": "kokoro", "voice": "af_heart", "speed": 1, "pitch": 0},
        "hash",
    )

    assert (tmp_path / "chunk_00001.wav").exists()
    assert (tmp_path / "chunk_00002.wav").exists()
    assert not (tmp_path / "chunk_00003.wav").exists()


def test_resume_rejects_valid_audio_that_changed_after_manifest(tmp_path):
    manager = ResumeManager(tmp_path)
    settings = {
        "engine": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
        "pitch": 0.0,
        "engine_fingerprint": {"package_version": "1"},
    }
    manager.begin(1, tmp_path / "book.pdf", settings, "book-hash")
    wav = tmp_path / "chunk_00001.wav"
    write_wav(wav, frames=6000)
    manager.mark_completed(1, 1, "Hello.", settings, wav)

    write_wav(wav, frames=7000)
    assert not manager.is_current(1, "Hello.", settings, wav)


def test_resume_fingerprint_changes_when_engine_runtime_changes(tmp_path):
    manager = ResumeManager(tmp_path)
    first = {
        "engine": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
        "pitch": 0.0,
        "engine_fingerprint": {"package_version": "1"},
    }
    second = {**first, "engine_fingerprint": {"package_version": "2"}}
    wav = tmp_path / "chunk_00001.wav"
    manager.begin(1, tmp_path / "book.pdf", first, "book-hash")
    write_wav(wav)
    manager.mark_completed(1, 1, "Hello.", first, wav)
    assert manager.is_current(1, "Hello.", first, wav)
    assert not manager.is_current(1, "Hello.", second, wav)


def test_r1173_invalidates_pre_repair_chunk_manifests(tmp_path):
    import json

    old_manifest = {
        "schema": 2,
        "chunks": {
            "1": {"hash": "old-regressed-audio", "file": "chunk_00001.wav"}
        },
    }
    (tmp_path / ResumeManager.MANIFEST_NAME).write_text(
        json.dumps(old_manifest), encoding="utf-8"
    )
    manager = ResumeManager(tmp_path)
    loaded = manager.load_manifest()
    assert ResumeManager.SCHEMA_VERSION == 3
    assert loaded["schema"] == 3
    assert loaded["chunks"] == {}
