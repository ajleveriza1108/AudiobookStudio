from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def test_qt_runtime_uses_published_python312_wheel_version():
    requirements = read("requirements.txt")
    repair = read("repair_gui_runtime.ps1")
    health = read("Scripts/runtime_health.py")
    assert "PySide6==6.8.3" in requirements
    assert '$TargetVersion = "6.8.3"' in repair
    assert '"PySide6==$TargetVersion"' in repair
    assert 'version != "6.8.3"' in health
    assert "6.8.7" not in requirements + repair + health
    assert "--only-binary=:all:" in repair


def test_gui_runtime_repair_is_transactional():
    repair = read("repair_gui_runtime.ps1")
    assert "PreviousVersion" in repair
    assert "Restore-PreviousQtRuntime" in repair
    assert "PySide6==$PreviousVersion" in repair
    assert "?" not in repair  # Windows PowerShell 5.1 has no ternary operator.


def test_application_uses_safe_windows_rendering_and_deferred_restore():
    app = read("app.py")
    assert 'QT_STYLE_OVERRIDE", "Fusion"' in app
    assert 'QT_OPENGL", "software"' in app
    assert 'self.app.setStyle("Fusion")' in app
    assert "RoundPreferFloor" in app
    assert "QTimer.singleShot(500, self.restore_document_session)" in app
    assert "startup_stage.json" in app
    assert "faulthandler.enable" in app


def test_cover_preview_avoids_native_pixmap_repaint_path():
    source = read("ui/preview_cover.py")
    assert "QPixmap" not in source
    assert "QTimer" not in source
    assert "setPixmap" not in source
    assert "resizeEvent" not in source
    assert "showEvent" not in source


def test_real_windows_probe_is_required_before_success():
    repair = read("repair_gui_runtime.ps1")
    verifier = read("verify_phase3.py")
    probe = read("Scripts/gui_startup_probe.py")
    assert "gui_startup_probe.py" in repair
    assert '"--visible-ms", "8000"' in repair
    assert "gui_startup_probe.py" in verifier
    assert 'env.pop("QT_QPA_PLATFORM", None)' in probe
