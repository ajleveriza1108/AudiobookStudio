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
    "window_width": 1366,
    "window_height": 768,
    "window_maximized": False,
    "remember_last_book": True,
    "last_book": "",
    "last_books": [],
    "removed_books": [],
    "auto_merge": True,
    "resume_generation": True,
    "validate_chunks": True,
    "delete_chunks": False,
    "export_wav": True,
    "export_mp3": False,
    "export_m4b": False,
    "bitrate": "192k",
    "sample_rate": 24000,
    "panel_library_visible": True,
    "panel_settings_visible": True,
    "panel_activity_visible": True,
    "focus_side_panel": "settings",
    "processing_device": "auto",
    "gpu_runtime_enabled": True,
    "gpu_runtime_status": "not_installed",
    "gpu_runtime_report": "",
    "advanced_ocr_enabled": False,
    "advanced_ocr_status": "not_checked",
    "advanced_ocr_can_enable": False,
    "advanced_ocr_last_checked_at": "",
    "advanced_ocr_report": "",
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

    @staticmethod
    def _book_path(value: str | Path) -> str:
        return str(Path(value).expanduser().resolve())

    @classmethod
    def _book_key(cls, value: str | Path) -> str:
        return os.path.normcase(cls._book_path(value))

    def append_recent_book(self, book: str | Path) -> None:
        book_path = self._book_path(book)
        book_key = self._book_key(book_path)

        with self._lock:
            books = [
                self._book_path(item)
                for item in self.data.get("last_books", [])
                if isinstance(item, (str, Path))
            ]
            books = [item for item in books if self._book_key(item) != book_key]
            books.insert(0, book_path)

            removed = [
                self._book_path(item)
                for item in self.data.get("removed_books", [])
                if isinstance(item, (str, Path))
            ]
            removed = [item for item in removed if self._book_key(item) != book_key]

            self.data["last_books"] = books[:20]
            self.data["last_book"] = book_path
            self.data["removed_books"] = removed[:200]
            self.save()

    def remove_recent_book(self, book: str | Path) -> None:
        book_path = self._book_path(book)
        book_key = self._book_key(book_path)

        with self._lock:
            books = [
                self._book_path(item)
                for item in self.data.get("last_books", [])
                if isinstance(item, (str, Path))
            ]
            books = [item for item in books if self._book_key(item) != book_key]

            removed = [
                self._book_path(item)
                for item in self.data.get("removed_books", [])
                if isinstance(item, (str, Path))
            ]
            if all(self._book_key(item) != book_key for item in removed):
                removed.insert(0, book_path)

            last_book = str(self.data.get("last_book", "") or "")
            if last_book and self._book_key(last_book) == book_key:
                last_book = ""

            self.data["last_books"] = books[:20]
            self.data["last_book"] = last_book
            self.data["removed_books"] = removed[:200]
            self.save()

    def is_book_removed(self, book: str | Path) -> bool:
        book_key = self._book_key(book)
        with self._lock:
            return any(
                self._book_key(item) == book_key
                for item in self.data.get("removed_books", [])
                if isinstance(item, (str, Path))
            )

    def recent_books(self) -> list[str]:
        with self._lock:
            removed = {
                self._book_key(item)
                for item in self.data.get("removed_books", [])
                if isinstance(item, (str, Path))
            }
            values = self.data.get("last_books", [])
            result: list[str] = []
            for value in values:
                if not isinstance(value, (str, Path)):
                    continue
                path = self._book_path(value)
                if self._book_key(path) not in removed:
                    result.append(path)
            return result

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self.data)
