from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

from core.paths import PATHS


VOICE_FILE = PATHS.project_root / "voices.json"
DEFAULT: dict[str, dict[str, Any]] = {
    "Default": {
        "engine": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
        "pitch": 0.0,
    }
}


class VoiceProfiles:
    """Local narrator profiles stored beside the portable application."""

    def __init__(self, file: str | Path | None = None):
        self.file = Path(file or VOICE_FILE)
        self.data: dict[str, dict[str, Any]] = {}
        self._lock = RLock()
        self.load()

    def load(self) -> None:
        with self._lock:
            if not self.file.is_file():
                self.data = deepcopy(DEFAULT)
                self.save()
                return
            try:
                loaded = json.loads(self.file.read_text(encoding="utf-8-sig"))
                if not isinstance(loaded, dict):
                    raise ValueError("Voice profiles must contain a JSON object.")
                self.data = {
                    str(name): dict(profile)
                    for name, profile in loaded.items()
                    if isinstance(profile, dict)
                }
                if "Default" not in self.data:
                    self.data["Default"] = deepcopy(DEFAULT["Default"])
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                self.data = deepcopy(DEFAULT)

    def save(self) -> None:
        with self._lock:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(self.file.suffix + ".tmp")
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.file)

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self.data, key=str.casefold)

    def add(self, name, engine, voice, speed, pitch) -> None:
        profile_name = str(name).strip()
        if not profile_name:
            raise ValueError("A profile name is required.")
        with self._lock:
            self.data[profile_name] = {
                "engine": str(engine or "kokoro"),
                "voice": str(voice or "af_heart"),
                "speed": float(speed),
                "pitch": float(pitch),
            }
            self.save()

    def remove(self, name) -> None:
        profile_name = str(name)
        if profile_name == "Default":
            return
        with self._lock:
            if profile_name in self.data:
                del self.data[profile_name]
                self.save()

    def get(self, name) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self.data.get(str(name), DEFAULT["Default"]))
