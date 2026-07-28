from __future__ import annotations

from pathlib import Path
from typing import Any

from core.resume import ResumeManager


class ProgressManager:
    """Backward-compatible progress.json helper."""

    FILE_NAME = "progress.json"

    def __init__(self, project_folder):
        self.project_folder = Path(project_folder)
        self.resume = ResumeManager(self.project_folder)
        self.file = self.resume.file

    def load(self):
        return self.resume.load()

    def save(self, chunk, total, chapter, wav):
        state: dict[str, Any] = self.resume.load() or {}
        state["wav"] = str(wav)
        self.resume.save(chunk, total, chapter)
        # save() writes the compatible fields. wav is optional legacy detail.
        updated = self.resume.load() or state
        updated["wav"] = str(wav)
        self.resume._atomic_write(self.file, updated)

    def clear(self):
        self.resume.clear()
