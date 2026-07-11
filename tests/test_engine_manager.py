import json
from pathlib import Path

import pytest

from engines.manager import EngineManager


def test_builtin_engines_are_registered(tmp_path: Path) -> None:
    manager = EngineManager(manifest_dir=tmp_path)
    assert {"kokoro", "piper", "xtts"}.issubset(set(manager.names()))


def test_manifest_can_disable_engine(tmp_path: Path) -> None:
    manifest = {
        "id": "kokoro",
        "name": "Kokoro",
        "module": "engines.kokoro",
        "class": "KokoroEngine",
        "enabled": False,
    }
    (tmp_path / "kokoro.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    manager = EngineManager(manifest_dir=tmp_path)
    assert "kokoro" not in manager.names()
    assert "kokoro" in manager.names(include_disabled=True)


def test_unknown_engine_has_clear_error(tmp_path: Path) -> None:
    manager = EngineManager(manifest_dir=tmp_path)

    with pytest.raises(ValueError, match="Unknown engine"):
        manager.manifest("does-not-exist")
