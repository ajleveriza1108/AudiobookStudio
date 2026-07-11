from pathlib import Path

from core.paths import AppPaths


def test_discover_from_core_folder(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "core").mkdir()
    (tmp_path / "engines").mkdir()

    paths = AppPaths.discover(tmp_path / "core")
    assert paths.project_root == tmp_path.resolve()
    assert paths.output == tmp_path.resolve() / "Output"


def test_resolve_relative_path(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("", encoding="utf-8")
    (tmp_path / "core").mkdir()
    (tmp_path / "engines").mkdir()

    paths = AppPaths.discover(tmp_path)
    assert paths.resolve("Output") == (tmp_path / "Output").resolve()
