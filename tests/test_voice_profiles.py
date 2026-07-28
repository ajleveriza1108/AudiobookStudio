import json

from core.voice_profiles import VoiceProfiles


def test_voice_profiles_use_atomic_portable_storage(tmp_path):
    path = tmp_path / "voices.json"
    profiles = VoiceProfiles(path)
    profiles.add("Reader", "kokoro", "am_adam", 0.95, -1)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["Reader"]["voice"] == "am_adam"
    assert VoiceProfiles(path).get("Reader")["speed"] == 0.95
