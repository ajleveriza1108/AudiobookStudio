from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

from core.optional_engines import chatterbox_runtime_ready
from core.paths import PATHS
from engines.manifest import EngineManifest


class EngineManager:
    """Discovers TTS engines from engines/manifests/*.json."""

    def __init__(self, manifest_dir: str | Path | None = None) -> None:
        self.manifest_dir = Path(manifest_dir or PATHS.engine_manifests)
        self.manifests: dict[str, EngineManifest] = {}
        self.errors: list[dict[str, str]] = []
        self.reload()

    @staticmethod
    def _builtin_manifests() -> list[EngineManifest]:
        return [
            EngineManifest.from_mapping(
                {
                    "id": "kokoro",
                    "name": "Kokoro",
                    "module": "engines.kokoro",
                    "class": "KokoroEngine",
                    "default_voice": "af_heart",
                    "dependencies": ["kokoro", "torch", "numpy", "soundfile"],
                    "capabilities": {
                        "voice_cloning": False,
                        "multilingual": True,
                        "streaming": True,
                        "pitch_control": True,
                    },
                }
            ),
            EngineManifest.from_mapping(
                {
                    "id": "piper",
                    "name": "Piper",
                    "module": "engines.piper",
                    "class": "PiperEngine",
                    "enabled": False,
                    "dependencies": [],
                    "capabilities": {
                        "voice_cloning": False,
                        "multilingual": True,
                        "streaming": False,
                        "pitch_control": False,
                    },
                }
            ),
            EngineManifest.from_mapping(
                {
                    "id": "chatterbox",
                    "name": "Chatterbox Voice Cloning",
                    "module": "engines.chatterbox",
                    "class": "ChatterboxEngine",
                    "enabled": True,
                    "priority": 80,
                    "default_voice": "",
                    "dependencies": [],
                    "capabilities": {
                        "voice_cloning": True,
                        "multilingual": True,
                        "streaming": False,
                        "pitch_control": True,
                    },
                }
            ),
            EngineManifest.from_mapping(
                {
                    "id": "xtts",
                    "name": "XTTS",
                    "module": "engines.xtts",
                    "class": "XTTSEngine",
                    "enabled": False,
                    "dependencies": ["TTS"],
                    "capabilities": {
                        "voice_cloning": True,
                        "multilingual": True,
                        "streaming": False,
                        "pitch_control": False,
                    },
                }
            ),
        ]

    def reload(self) -> None:
        self.manifests = {
            manifest.id: manifest
            for manifest in self._builtin_manifests()
        }
        self.errors.clear()
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

        for path in sorted(self.manifest_dir.glob("*.json")):
            try:
                manifest = EngineManifest.from_file(path)
                self.manifests[manifest.id] = manifest
            except Exception as error:
                self.errors.append(
                    {
                        "path": str(path),
                        "error": str(error),
                        "type": error.__class__.__name__,
                    }
                )

    def names(self, include_disabled: bool = False) -> list[str]:
        manifests = sorted(
            self.manifests.values(),
            key=lambda item: (-item.priority, item.name.casefold()),
        )
        return [
            manifest.id
            for manifest in manifests
            if include_disabled or manifest.enabled
        ]

    def manifest(self, name: str) -> EngineManifest:
        key = str(name).strip().lower()
        try:
            return self.manifests[key]
        except KeyError as error:
            choices = ", ".join(self.names())
            raise ValueError(f"Unknown engine '{name}'. Available: {choices}") from error

    @staticmethod
    def _missing_dependencies(manifest: EngineManifest) -> list[str]:
        if manifest.id == "chatterbox":
            return [] if chatterbox_runtime_ready() else ["optional Chatterbox module"]

        missing: list[str] = []

        for dependency in manifest.dependencies:
            module_name = dependency.split("[", 1)[0].replace("-", "_")
            try:
                found = importlib.util.find_spec(module_name)
            except (ImportError, ModuleNotFoundError, ValueError):
                found = None

            if found is None:
                missing.append(dependency)

        return missing

    def create(self, name: str):
        manifest = self.manifest(name)

        if not manifest.enabled:
            raise RuntimeError(f"Engine '{manifest.id}' is disabled.")

        missing = self._missing_dependencies(manifest)
        if missing:
            raise RuntimeError(
                f"Engine '{manifest.id}' is missing dependencies: "
                + ", ".join(missing)
            )

        try:
            module = importlib.import_module(manifest.module)
            engine_class = getattr(module, manifest.class_name)
            engine = engine_class()
        except Exception as error:
            raise RuntimeError(
                f"Could not load engine '{manifest.id}' "
                f"from {manifest.module}:{manifest.class_name}: {error}"
            ) from error

        for method in ("speak", "available_voices", "backend", "gpu_name"):
            if not callable(getattr(engine, method, None)):
                raise TypeError(
                    f"Engine '{manifest.id}' does not implement required method '{method}'."
                )

        return engine

    @staticmethod
    def _hardware() -> tuple[str, str]:
        try:
            import torch

            if torch.cuda.is_available():
                return "CUDA", torch.cuda.get_device_name(0)
        except Exception:
            pass

        return "CPU", "CPU"

    def available(self) -> list[dict[str, Any]]:
        backend, gpu = self._hardware()
        results: list[dict[str, Any]] = []

        for name in self.names(include_disabled=True):
            manifest = self.manifests[name]
            missing = self._missing_dependencies(manifest)

            if not manifest.enabled:
                status = "Disabled"
            elif missing:
                status = "Unavailable"
            else:
                status = "Available"

            results.append(
                {
                    "name": manifest.id,
                    "display_name": manifest.name,
                    "status": status,
                    "backend": backend if status == "Available" else "Unavailable",
                    "gpu": gpu if status == "Available" else "Unavailable",
                    "missing_dependencies": missing,
                    "default_voice": manifest.default_voice,
                    "capabilities": dict(manifest.capabilities),
                }
            )

        return results

    def metadata(self, name: str) -> dict[str, Any]:
        manifest = self.manifest(name)
        data = manifest.to_dict()
        data["missing_dependencies"] = self._missing_dependencies(manifest)
        return data
