from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EngineManifest:
    id: str
    name: str
    module: str
    class_name: str
    enabled: bool = True
    priority: int = 50
    default_voice: str = ""
    language: str = "en"
    dependencies: tuple[str, ...] = ()
    capabilities: dict[str, Any] = field(default_factory=dict)
    source: Path | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "EngineManifest":
        manifest_path = Path(path)
        with manifest_path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(f"Manifest must contain a JSON object: {manifest_path}")

        return cls.from_mapping(data, source=manifest_path)

    @classmethod
    def from_mapping(
        cls,
        data: dict[str, Any],
        source: str | Path | None = None,
    ) -> "EngineManifest":
        engine_id = str(data.get("id", "")).strip().lower()
        module = str(data.get("module", "")).strip()
        class_name = str(data.get("class", data.get("class_name", ""))).strip()

        if not engine_id:
            raise ValueError("Engine manifest is missing 'id'.")
        if not module:
            raise ValueError(f"Engine '{engine_id}' is missing 'module'.")
        if not class_name:
            raise ValueError(f"Engine '{engine_id}' is missing 'class'.")

        raw_dependencies = data.get("dependencies", [])
        if not isinstance(raw_dependencies, list):
            raise ValueError(f"Engine '{engine_id}' dependencies must be a list.")

        capabilities = data.get("capabilities", {})
        if not isinstance(capabilities, dict):
            capabilities = {}

        return cls(
            id=engine_id,
            name=str(data.get("name") or engine_id).strip(),
            module=module,
            class_name=class_name,
            enabled=bool(data.get("enabled", True)),
            priority=int(data.get("priority", 50)),
            default_voice=str(data.get("default_voice", "")).strip(),
            language=str(data.get("language", "en")).strip(),
            dependencies=tuple(str(item).strip() for item in raw_dependencies if str(item).strip()),
            capabilities=dict(capabilities),
            source=Path(source).resolve() if source else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "module": self.module,
            "class": self.class_name,
            "enabled": self.enabled,
            "priority": self.priority,
            "default_voice": self.default_voice,
            "language": self.language,
            "dependencies": list(self.dependencies),
            "capabilities": dict(self.capabilities),
            "source": str(self.source) if self.source else None,
        }
