from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


class Exporter:
    @staticmethod
    def _atomic_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def save_project(self, folder, metadata):
        root = Path(folder)
        data = dict(metadata)
        data["saved"] = datetime.now(timezone.utc).isoformat()
        self._atomic_json(root / "project.json", data)

    def load_project(self, folder):
        file = Path(folder) / "project.json"
        if not file.is_file():
            return {}
        try:
            data = json.loads(file.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def export_metadata(self, folder, metadata):
        self._atomic_json(Path(folder) / "metadata.json", dict(metadata))

    def export_chapters(self, folder, chapters):
        self._atomic_json(Path(folder) / "chapters.json", list(chapters))

    def export_narration_plan(self, folder, plan):
        self._atomic_json(Path(folder) / "narration_plan.json", list(plan))

    def export_preparation_report(self, folder, report):
        self._atomic_json(Path(folder) / "preparation_report.json", dict(report))
