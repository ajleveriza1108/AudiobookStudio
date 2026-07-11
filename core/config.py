from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

from core.paths import PATHS


CONFIG_FILE = PATHS.config_local
DEFAULT_CONFIG_FILE = PATHS.config_defaults

DEFAULT_CONFIG: dict[str, Any] = {
    "engine": "kokoro",
    "voice": "af_heart",
    "speed": 1.0,
    "pitch": 0.0,
    "theme": "dark",
    "output_folder": "Output",
    "project_folder": "Projects",
    "cache_folder": "Cache",
    "model_folder": "Models",
    "logs_folder": "Logs",
    "window_width": 1536,
    "window_height": 864,
    "window_maximized": False,
    "remember_last_book": True,
    "last_book": "",
    "last_books": [],
    "auto_merge": True,
    "resume_generation": True,
    "validate_chunks": True,
    "delete_chunks": False,
    "export_wav": True,
    "export_mp3": False,
    "export_m4b": False,
    "bitrate": "192k",
    "sample_rate": 24000,
}


class Config:
    """
    Layered configuration.

    config.json is the repository-safe default file.
    config.local.json stores machine-specific and private user settings.
    """

    def __init__(
        self,
        defaults_file: str | Path | None = None,
        user_file: str | Path | None = None,
    ) -> None:
        PATHS.ensure_runtime_directories()
        self.defaults_file = Path(defaults_file or DEFAULT_CONFIG_FILE)
        self.user_file = Path(user_file or CONFIG_FILE)
        self._lock = RLock()
        self.data: dict[str, Any] = {}
        self.load()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}

        with path.open("r", encoding="utf-8-sig") as file:
            loaded = json.load(file)

        if not isinstance(loaded, dict):
            raise ValueError(f"Expected a JSON object in {path}")

        return loaded

    def load(self) -> None:
        with self._lock:
            data = deepcopy(DEFAULT_CONFIG)

            try:
                data.update(self._read_json(self.defaults_file))
            except (OSError, ValueError, json.JSONDecodeError):
                # Invalid defaults must not prevent the GUI from starting.
                pass

            try:
                data.update(self._read_json(self.user_file))
            except (OSError, ValueError, json.JSONDecodeError):
                self._quarantine_invalid_user_file()

            self.data = data

    def _quarantine_invalid_user_file(self) -> None:
        if not self.user_file.exists():
            return

        backup = self.user_file.with_suffix(self.user_file.suffix + ".invalid")
        try:
            os.replace(self.user_file, backup)
        except OSError:
            pass

    def save(self) -> None:
        with self._lock:
            self.user_file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.user_file.with_suffix(self.user_file.suffix + ".tmp")

            with temporary.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(self.data, file, indent=2, ensure_ascii=False)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary, self.user_file)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self.data[key] = str(value) if isinstance(value, Path) else value
            self.save()

    def update(self, values: dict[str, Any], save: bool = True) -> None:
        with self._lock:
            self.data.update(values)
            if save:
                self.save()

    def append_recent_book(self, book: str | Path) -> None:
        book_path = str(Path(book).expanduser().resolve())

        with self._lock:
            books = [
                str(item)
                for item in self.data.get("last_books", [])
                if isinstance(item, (str, Path))
            ]
            books = [item for item in books if item != book_path]
            books.insert(0, book_path)

            self.data["last_books"] = books[:20]
            self.data["last_book"] = book_path
            self.save()

    def recent_books(self) -> list[str]:
        with self._lock:
            values = self.data.get("last_books", [])
            return [str(value) for value in values if isinstance(value, (str, Path))]

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self.data)
