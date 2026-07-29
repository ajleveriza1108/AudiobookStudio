from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any

from core.chunk_validator import ChunkValidator


class ResumeManager:
    """Tracks crash recovery and validates reusable narration chunks."""

    FILE_NAME = "progress.json"
    MANIFEST_NAME = "chunk_manifest.json"
    SCHEMA_VERSION = 3

    def __init__(self, output_folder: str | Path | None = None):
        self.output = Path(output_folder or ".")
        self.file = self.output / self.FILE_NAME
        self.manifest_file = self.output / self.MANIFEST_NAME
        self._lock = RLock()
        self._manifest: dict[str, Any] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _atomic_write(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)

    @staticmethod
    def text_hash(text: str) -> str:
        return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

    @classmethod
    def chunk_hash(cls, text: str, settings: dict[str, Any]) -> str:
        stable = {
            "text": str(text),
            "engine": str(settings.get("engine", "kokoro")),
            "voice": str(settings.get("voice", "")),
            "speed": round(float(settings.get("speed", 1.0)), 4),
            "pitch": round(float(settings.get("pitch", 0.0)), 4),
            "engine_fingerprint": settings.get("engine_fingerprint", {}),
        }
        encoded = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def exists(self):
        return self.file.is_file()

    def load(self):
        return self._read_json(self.file) or None

    def load_manifest(self) -> dict[str, Any]:
        with self._lock:
            if not self._manifest:
                self._manifest = self._read_json(self.manifest_file)
            if self._manifest.get("schema") != self.SCHEMA_VERSION:
                self._manifest = {
                    "schema": self.SCHEMA_VERSION,
                    "chunks": {},
                    "updated": self._now(),
                }
            self._manifest.setdefault("chunks", {})
            return self._manifest

    def begin(
        self,
        total_chunks: int,
        source: str | Path,
        settings: dict[str, Any],
        text_hash: str,
    ) -> None:
        with self._lock:
            self.output.mkdir(parents=True, exist_ok=True)
            manifest = self.load_manifest()
            manifest.update(
                {
                    "schema": self.SCHEMA_VERSION,
                    "source": str(Path(source)),
                    "text_hash": text_hash,
                    "settings": dict(settings),
                    "total": int(total_chunks),
                    "updated": self._now(),
                }
            )

            # Remove leftover sections when the newly prepared book contains
            # fewer chunks than an earlier run. Without this, an old tail could
            # be appended to the new audiobook during merge.
            for wav_file in ChunkValidator.ordered(self.output):
                number = ChunkValidator.number(wav_file)
                if number is not None and number > int(total_chunks):
                    wav_file.unlink(missing_ok=True)

            for key in list(manifest.get("chunks", {})):
                try:
                    number = int(key)
                except ValueError:
                    manifest["chunks"].pop(key, None)
                    continue
                if number > int(total_chunks):
                    manifest["chunks"].pop(key, None)

            self._atomic_write(self.manifest_file, manifest)
            self._atomic_write(
                self.file,
                {
                    "schema": self.SCHEMA_VERSION,
                    "status": "running",
                    "source": str(Path(source)),
                    "total": int(total_chunks),
                    "completed": 0,
                    "current_chunk": 0,
                    "text_hash": text_hash,
                    "settings": dict(settings),
                    "updated": self._now(),
                },
            )

    def is_current(
        self,
        index: int,
        text: str,
        settings: dict[str, Any],
        wav_file: str | Path,
    ) -> bool:
        path = Path(wav_file)
        if not ChunkValidator.valid(path):
            if path.exists():
                path.unlink(missing_ok=True)
            return False

        manifest = self.load_manifest()
        record = manifest.get("chunks", {}).get(str(int(index)), {})
        expected = self.chunk_hash(text, settings)
        details = ChunkValidator.inspect(path)
        recorded_audio = {
            "size": record.get("size"),
            "frames": record.get("frames"),
            "sample_rate": record.get("sample_rate"),
            "channels": record.get("channels"),
            "sample_width": record.get("sample_width"),
        }
        current_audio = {
            "size": details.get("size"),
            "frames": details.get("frames"),
            "sample_rate": details.get("sample_rate"),
            "channels": details.get("channels"),
            "sample_width": details.get("sample_width"),
        }
        return bool(
            record.get("hash") == expected
            and record.get("file") == path.name
            and recorded_audio == current_audio
        )

    def mark_completed(
        self,
        index: int,
        total: int,
        text: str,
        settings: dict[str, Any],
        wav_file: str | Path,
    ) -> None:
        path = Path(wav_file)
        details = ChunkValidator.inspect(path)
        if not details["valid"]:
            raise RuntimeError(f"Generated audio chunk is invalid: {path.name}")

        with self._lock:
            manifest = self.load_manifest()
            manifest["chunks"][str(int(index))] = {
                "hash": self.chunk_hash(text, settings),
                "file": path.name,
                "size": details["size"],
                "frames": details["frames"],
                "sample_rate": details["sample_rate"],
                "channels": details["channels"],
                "sample_width": details["sample_width"],
                "updated": self._now(),
            }
            manifest["updated"] = self._now()
            self._atomic_write(self.manifest_file, manifest)

            state = self._read_json(self.file)
            state.update(
                {
                    "schema": self.SCHEMA_VERSION,
                    "status": "running",
                    "total": int(total),
                    "completed": int(index),
                    "current_chunk": int(index),
                    "wav": str(path),
                    "updated": self._now(),
                }
            )
            self._atomic_write(self.file, state)

    def save(self, current_chunk, total_chunks, current_chapter=0):
        """Compatibility method retained for older callers."""
        state = self._read_json(self.file)
        state.update(
            {
                "schema": self.SCHEMA_VERSION,
                "status": "running",
                "current_chunk": int(current_chunk),
                "completed": int(current_chunk),
                "total": int(total_chunks),
                "chapter": int(current_chapter),
                "updated": self._now(),
            }
        )
        self._atomic_write(self.file, state)

    def finish(self) -> None:
        self.clear()

    def clear(self):
        with self._lock:
            self.file.unlink(missing_ok=True)

    def remove(self, output_folder: str | Path | None = None):
        if output_folder is not None:
            ResumeManager(output_folder).clear()
        else:
            self.clear()
