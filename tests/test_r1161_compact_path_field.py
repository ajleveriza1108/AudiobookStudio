from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_compact_path_field_does_not_call_q_label_api():
    source = (ROOT / "ui" / "compact_widgets.py").read_text(encoding="utf-8")
    assert "class CompactPathField(QLineEdit)" in source
    assert "setTextInteractionFlags" not in source
    assert "setReadOnly(True)" in source
    assert "setFocusPolicy(Qt.FocusPolicy.StrongFocus)" in source


def test_r1161_version_contract():
    source = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    assert 'R1.' in source
    assert "BUILD =" in source


def test_compact_path_field_constructs_with_real_pyside():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from ui.compact_widgets import CompactPathField

    app = QApplication.instance() or QApplication([])
    field = CompactPathField("No book selected")
    assert field.isReadOnly()
    field.setValue(r"D:\Books\Example.pdf")
    assert field.text().endswith("Example.pdf")
    field.selectAll()
    assert field.selectedText() == field.text()
