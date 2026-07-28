from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_gui_dispatch_probe_guards_deleted_qthread_wrapper():
    source = (ROOT / "Scripts" / "gui_thread_dispatch_probe.py").read_text(encoding="utf-8")
    assert "from shiboken6 import isValid as is_qt_object_valid" in source
    assert "def qt_object_is_alive" in source
    assert "def request_thread_stop" in source
    assert "request_thread_stop(thread, wait_ms=5000)" in source
    assert "delete_later_if_alive(thread)" in source


def test_probe_has_no_unconditional_post_event_loop_qthread_cleanup():
    source = (ROOT / "Scripts" / "gui_thread_dispatch_probe.py").read_text(encoding="utf-8")
    tail = source.split("application.exec()", 1)[1]
    assert "\n    thread.quit()\n" not in tail
    assert "\n    thread.wait(" not in tail
    assert "\n    thread.deleteLater()\n" not in tail
