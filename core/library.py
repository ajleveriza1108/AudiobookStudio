from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from core.paths import PATHS


DATABASE = PATHS.library_local
LEGACY_DATABASE = PATHS.library_legacy


class Library:
    """Portable, private audiobook library stored in library.local.json."""

    def __init__(self, database: str | Path | None = None) -> None:
        PATHS.ensure_runtime_directories()
        self.database = Path(database or DATABASE)
        self._lock = RLock()
        self.books: list[dict[str, Any]] = []
        self.load()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8-sig") as file:
            loaded = json.load(file)

        if not isinstance(loaded, list):
            raise ValueError("Library must contain a JSON list.")

        return [item for item in loaded if isinstance(item, dict)]

    def load(self) -> None:
        with self._lock:
            source = self.database

            # One-time compatibility migration from the old tracked library.json.
            if not source.exists() and LEGACY_DATABASE.exists():
                source = LEGACY_DATABASE

            if not source.exists():
                self.books = []
                self.save()
                return

            try:
                self.books = self._read(source)
            except (OSError, ValueError, json.JSONDecodeError):
                self.books = []

            if source != self.database:
                self.save()

    def save(self) -> None:
        with self._lock:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.database.with_suffix(self.database.suffix + ".tmp")

            with temporary.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(self.books, file, indent=2, ensure_ascii=False)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary, self.database)

    @staticmethod
    def checksum(file: str | Path) -> str:
        path = Path(file)
        digest = hashlib.sha256()

        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)

        return digest.hexdigest()

    def add(self, file: str | Path) -> bool:
        path = Path(file).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)

        checksum = self.checksum(path)

        with self._lock:
            for book in self.books:
                if book.get("checksum") == checksum:
                    return False

            self.books.append(
                {
                    "title": path.stem,
                    "path": str(path),
                    "checksum": checksum,
                    "favorite": False,
                    "created": self._now(),
                    "last_opened": None,
                    "completed": False,
                    "progress": 0,
                    "engine": "kokoro",
                    "voice": "af_heart",
                    "tags": [],
                }
            )
            self.save()
            return True

    def remove(self, path: str | Path) -> None:
        target = str(Path(path).expanduser().resolve())
        with self._lock:
            self.books = [
                book
                for book in self.books
                if str(book.get("path", "")) != target
            ]
            self.save()

    def update_progress(self, path: str | Path, percent: int | float) -> None:
        target = str(Path(path).expanduser().resolve())
        value = max(0, min(100, int(percent)))

        with self._lock:
            for book in self.books:
                if str(book.get("path", "")) == target:
                    book["progress"] = value
                    book["completed"] = value >= 100
                    break
            self.save()

    def touch(self, path: str | Path) -> None:
        target = str(Path(path).expanduser().resolve())

        with self._lock:
            for book in self.books:
                if str(book.get("path", "")) == target:
                    book["last_opened"] = self._now()
                    break
            self.save()

    def favorite(self, path: str | Path) -> None:
        target = str(Path(path).expanduser().resolve())

        with self._lock:
            for book in self.books:
                if str(book.get("path", "")) == target:
                    book["favorite"] = not bool(book.get("favorite", False))
                    break
            self.save()

    def search(self, text: str) -> list[dict[str, Any]]:
        query = str(text).casefold()
        with self._lock:
            return [
                dict(book)
                for book in self.books
                if query in str(book.get("title", "")).casefold()
            ]

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(book) for book in self.books]

    def recent(self) -> list[dict[str, Any]]:
        with self._lock:
            return sorted(
                (dict(book) for book in self.books),
                key=lambda item: str(item.get("last_opened") or ""),
                reverse=True,
            )

    def completed(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(book) for book in self.books if book.get("completed")]

    def unfinished(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(book) for book in self.books if not book.get("completed")]
