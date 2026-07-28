from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def test_cover_tile_has_no_native_pixmap_or_timer_repaint_path():
    source = read("ui/preview_cover.py")
    forbidden = [
        "QPixmap",
        "QImage",
        "QImageReader",
        "QTimer",
        "setPixmap",
        "resizeEvent",
        "showEvent",
        "paintEvent",
        "repaint(",
    ]
    for token in forbidden:
        assert token not in source
    assert "Cover artwork is temporarily disabled" in source


def test_probe_waits_until_after_document_restore_and_requires_marker():
    app = read("app.py")
    probe = read("Scripts/gui_startup_probe.py")
    assert "_schedule_probe_completion" in app
    assert "finally:" in app
    assert "post-restore-visible-dwell-complete" in app
    assert "auto_exit and not self._probe_mode" in app
    assert "gui_probe_complete.json" in probe
    assert "post-restore visible dwell" in probe
    assert "--visible-ms\", \"8000" in read("verify_phase3.py")


def test_unclean_shutdown_uses_safe_start_without_losing_library():
    app = read("app.py")
    assert "clean_shutdown.flag" in app
    assert "_PREVIOUS_SESSION_CLEAN" in app
    assert "safe-start-skipped-last-book" in app
    assert "self.sidebar.add_book(book)" in app
    assert "if self._previous_session_clean" in app


def test_runtime_status_updates_do_not_replace_widget_stylesheet():
    header = read("ui/header.py")
    section = header.split("def set_status", 1)[1]
    assert "setStyleSheet" not in section
    assert "self.status.setText" in section


def test_current_version_contract():
    version = read("core/version.py")
    checks = read("run_phase3_checks.ps1")
    assert "R1.16" in version
    assert "BUILD = 160" in version
    assert "R1.16" in checks
