from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from core.paths import PATHS


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
SUPPORTED_LANGUAGES = {
    "ar": "Arabic",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "sw": "Swahili",
    "tr": "Turkish",
    "zh": "Chinese",
}

VOICE_MODELS = {
    "nano": "Nano — smaller, English, CPU-friendly",
    "turbo": "Turbo — English, faster on a capable GPU",
    "multilingual-v3": "Multilingual V3 — larger, 23 languages",
}


@dataclass
class VoiceProfile:
    id: str
    name: str
    sample: str
    language: str = "en"
    authorized: bool = False
    notes: str = ""
    created_at: str = ""
    engine: str = "chatterbox"
    model: str = "nano"

    @classmethod
    def from_mapping(cls, value: dict) -> "VoiceProfile":
        return cls(
            id=str(value.get("id", "")).strip(),
            name=str(value.get("name", "")).strip(),
            sample=str(value.get("sample", "")).strip(),
            language=str(value.get("language", "en") or "en").strip().lower(),
            authorized=bool(value.get("authorized", False)),
            notes=str(value.get("notes", "") or ""),
            created_at=str(value.get("created_at", "") or ""),
            engine=str(value.get("engine", "chatterbox") or "chatterbox").strip().lower(),
            model=str(value.get("model", "nano") or "nano").strip().lower(),
        )


class VoiceLibrary:
    """Portable local voice-profile registry.

    The registry stores only user-authorized reference audio. It does not ship
    celebrity recordings, download voice samples, or silently clone a voice.
    """

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or (PATHS.voices / "Cloned")).resolve()
        self.index = self.root / "voice_profiles.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self._profiles: list[VoiceProfile] = []
        self.reload()

    @staticmethod
    def _safe_name(value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
        cleaned = cleaned.strip("._-")
        return cleaned[:80] or "voice_sample"

    def reload(self) -> None:
        try:
            data = json.loads(self.index.read_text(encoding="utf-8")) if self.index.is_file() else []
        except (OSError, json.JSONDecodeError):
            data = []
        if isinstance(data, dict):
            data = data.get("profiles", [])
        self._profiles = [
            VoiceProfile.from_mapping(item)
            for item in data
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ]

    def _save(self) -> None:
        payload = {
            "schema": 1,
            "profiles": [asdict(profile) for profile in self._profiles],
        }
        temporary = self.index.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.index)

    def all(self, *, authorized_only: bool = True, engine: str | None = None) -> list[VoiceProfile]:
        items = list(self._profiles)
        if authorized_only:
            items = [profile for profile in items if profile.authorized]
        if engine:
            wanted = str(engine).strip().lower()
            items = [profile for profile in items if profile.engine == wanted]
        return sorted(items, key=lambda item: item.name.casefold())

    def get(self, profile_id: str) -> VoiceProfile | None:
        wanted = str(profile_id or "").strip()
        return next((profile for profile in self._profiles if profile.id == wanted), None)

    def sample_path(self, profile_or_id: VoiceProfile | str) -> Path:
        profile = profile_or_id if isinstance(profile_or_id, VoiceProfile) else self.get(str(profile_or_id))
        if profile is None:
            raise KeyError(f"Unknown voice profile: {profile_or_id}")
        path = Path(profile.sample)
        if not path.is_absolute():
            path = self.root / path
        return path.resolve()

    def add(
        self,
        *,
        name: str,
        sample_file: str | Path,
        language: str = "en",
        authorized: bool,
        notes: str = "",
        engine: str = "chatterbox",
        model: str = "nano",
    ) -> VoiceProfile:
        if not authorized:
            raise ValueError("Permission confirmation is required before saving a voice profile.")

        source = Path(sample_file).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Reference recording not found: {source}")
        if source.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            choices = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            raise ValueError(f"Unsupported reference-audio type. Supported: {choices}")

        display_name = str(name or "").strip()
        if not display_name:
            raise ValueError("Enter a profile name.")

        selected_model = str(model or "nano").strip().lower()
        if selected_model not in VOICE_MODELS:
            raise ValueError(f"Unsupported voice model: {selected_model}")
        selected_language = str(language or "en").strip().lower()
        if selected_language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported narration language: {selected_language}")
        if selected_model in {"nano", "turbo"}:
            selected_language = "en"

        profile_id = uuid.uuid4().hex[:12]
        folder = self.root / profile_id
        folder.mkdir(parents=True, exist_ok=False)
        target = folder / self._safe_name(source.name)
        shutil.copy2(source, target)

        relative = target.relative_to(self.root).as_posix()
        profile = VoiceProfile(
            id=profile_id,
            name=display_name,
            sample=relative,
            language=selected_language,
            authorized=True,
            notes=str(notes or "").strip(),
            created_at=datetime.now().isoformat(timespec="seconds"),
            engine=str(engine or "chatterbox").strip().lower(),
            model=selected_model,
        )
        self._profiles.append(profile)
        self._save()
        return profile

    def update(
        self,
        profile_id: str,
        *,
        name: str | None = None,
        language: str | None = None,
        notes: str | None = None,
        model: str | None = None,
        authorized: bool | None = None,
        sample_file: str | Path | None = None,
    ) -> VoiceProfile:
        profile = self.get(profile_id)
        if profile is None:
            raise KeyError(f"Unknown voice profile: {profile_id}")
        if name is not None:
            value = str(name).strip()
            if not value:
                raise ValueError("Profile name cannot be empty.")
            profile.name = value
        if language is not None:
            selected_language = str(language or "en").strip().lower()
            if selected_language not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported narration language: {selected_language}")
            profile.language = selected_language
        if notes is not None:
            profile.notes = str(notes or "").strip()
        if authorized is not None:
            profile.authorized = bool(authorized)
        if sample_file is not None:
            source = Path(sample_file).expanduser().resolve()
            current = self.sample_path(profile)
            if source != current:
                if not source.is_file():
                    raise FileNotFoundError(f"Reference recording not found: {source}")
                if source.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
                    choices = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
                    raise ValueError(f"Unsupported reference-audio type. Supported: {choices}")
                target = current.parent / self._safe_name(source.name)
                shutil.copy2(source, target)
                if current != target:
                    try:
                        current.unlink()
                    except OSError:
                        pass
                profile.sample = target.relative_to(self.root).as_posix()
        if model is not None:
            selected = str(model or "nano").strip().lower()
            if selected not in VOICE_MODELS:
                raise ValueError(f"Unsupported voice model: {selected}")
            profile.model = selected
            if selected in {"nano", "turbo"}:
                profile.language = "en"
        self._save()
        return profile

    def remove(self, profile_id: str) -> bool:
        profile = self.get(profile_id)
        if profile is None:
            return False
        folder = self.sample_path(profile).parent
        self._profiles = [item for item in self._profiles if item.id != profile.id]
        self._save()
        try:
            shutil.rmtree(folder)
        except OSError:
            pass
        return True

    def ids(self, *, engine: str | None = None) -> list[str]:
        return [profile.id for profile in self.all(engine=engine)]

    def labels(self, *, engine: str | None = None) -> Iterable[tuple[str, str]]:
        for profile in self.all(engine=engine):
            language_name = SUPPORTED_LANGUAGES.get(profile.language, profile.language.upper())
            model_name = VOICE_MODELS.get(profile.model, profile.model).split(" — ", 1)[0]
            yield profile.id, f"{profile.name} — {language_name} · {model_name}"
