from pathlib import Path


def test_header_resize_modes_use_qt6_scoped_enums():
    root = Path(__file__).resolve().parents[1]
    chapter = (root / "ui" / "chapter_editor.py").read_text(encoding="utf-8")
    jobs = (root / "ui" / "job_monitor.py").read_text(encoding="utf-8")

    assert "horizontalHeader().ResizeToContents" not in chapter
    assert "horizontalHeader().Stretch" not in chapter
    assert "QHeaderView.ResizeMode.ResizeToContents" in chapter
    assert "QHeaderView.ResizeMode.Stretch" in chapter
    assert "QHeaderView.ResizeMode.Stretch" in jobs


def test_dependency_installer_uses_dedicated_runtime_repair():
    root = Path(__file__).resolve().parents[1]
    script = (root / "install_dependencies.ps1").read_text(encoding="utf-8")
    assert "repair_runtime.ps1" in script
    assert "ForceRebuild" in script
    assert "no .venv is required" not in script
