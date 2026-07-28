from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_paint_stable_cover_keeps_legacy_paths_injection_contract():
    pytest.importorskip("PySide6")
    import ui.preview_cover as module

    assert hasattr(module, "PATHS")
    source = Path(module.__file__).read_text(encoding="utf-8")
    for forbidden in ("QPixmap", "QImage", "QTimer", "setPixmap", "resizeEvent", "paintEvent"):
        assert forbidden not in source


def test_missing_book_uses_nonfatal_no_cover_tile(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from ui.preview_cover import PreviewCover

    app = QApplication.instance() or QApplication([])
    cover = PreviewCover()
    assert cover.load_cover(tmp_path / "missing.pdf") is False
    assert cover.text() == "No Cover"
    assert cover.last_error() == ""
    cover.deleteLater()
    app.processEvents()
