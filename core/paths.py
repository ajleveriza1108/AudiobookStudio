from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    """All application paths resolved from one portable project root.

    Keep every runtime directory in this one object so the GUI, workers, and
    command-line tools cannot drift into using different relative folders.
    """

    project_root: Path
    books: Path
    cache: Path
    output: Path
    projects: Path
    logs: Path
    models: Path
    temp: Path
    voices: Path
    config_defaults: Path
    config_local: Path
    library_legacy: Path
    library_local: Path
    engine_manifests: Path

    @classmethod
    def discover(cls, start: str | Path | None = None) -> "AppPaths":
        env_root = os.getenv("AUDIOBOOK_STUDIO_ROOT", "").strip()

        if env_root:
            project_root = Path(env_root).expanduser().resolve()
        elif getattr(sys, "frozen", False):
            project_root = Path(sys.executable).resolve().parent
        else:
            origin = Path(start).expanduser().resolve() if start else Path(__file__).resolve()
            if origin.is_file():
                origin = origin.parent
            project_root = cls._find_project_root(origin)

        return cls(
            project_root=project_root,
            books=project_root / "Books",
            cache=project_root / "Cache",
            output=project_root / "Output",
            projects=project_root / "Projects",
            logs=project_root / "Logs",
            models=project_root / "Models",
            temp=project_root / "Temp",
            voices=project_root / "Voices",
            config_defaults=project_root / "config.json",
            config_local=project_root / "config.local.json",
            library_legacy=project_root / "library.json",
            library_local=project_root / "library.local.json",
            engine_manifests=project_root / "engines" / "manifests",
        )

    @staticmethod
    def _find_project_root(origin: Path) -> Path:
        candidates = [origin, *origin.parents]
        for candidate in candidates:
            if (
                (candidate / "app.py").is_file()
                and (candidate / "core").is_dir()
                and (candidate / "engines").is_dir()
            ):
                return candidate.resolve()

        # core/paths.py normally lives one level below the project root.
        return Path(__file__).resolve().parent.parent

    def ensure_runtime_directories(self) -> None:
        for folder in (
            self.books,
            self.cache,
            self.output,
            self.projects,
            self.logs,
            self.models,
            self.temp,
            self.voices,
            self.engine_manifests,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    def resolve(self, value: str | Path) -> Path:
        """Resolve a user setting relative to the portable project root."""

        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.project_root / path
        return path.resolve()


PATHS = AppPaths.discover()
