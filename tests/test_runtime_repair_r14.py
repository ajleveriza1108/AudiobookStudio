from __future__ import annotations

import os
import re
from dataclasses import fields
from pathlib import Path

import fitz
import pytest

from core.batch import BatchProcessor, JobCollection
from core.paths import AppPaths


def _project_paths(root: Path) -> AppPaths:
    (root / "core").mkdir(parents=True, exist_ok=True)
    (root / "engines").mkdir(parents=True, exist_ok=True)
    (root / "app.py").write_text("# test project\n", encoding="utf-8")
    return AppPaths.discover(root)


def test_app_paths_declares_every_paths_attribute_used_by_source():
    project = Path(__file__).resolve().parents[1]
    declared = {field.name for field in fields(AppPaths)} | {
        "discover",
        "ensure_runtime_directories",
        "resolve",
    }
    referenced: set[str] = set()
    for source in project.rglob("*.py"):
        relative = source.relative_to(project)
        excluded = {".venv", ".gpu-venv", ".advanced-ocr-venv", "__pycache__", ".git"}
        if any(part in excluded for part in relative.parts):
            continue
        if relative.parts and relative.parts[0].startswith("_backup_"):
            continue
        if "site-packages" in relative.parts:
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        referenced.update(re.findall(r"PATHS\.([A-Za-z_][A-Za-z0-9_]*)", text))

    assert referenced <= declared, sorted(referenced - declared)
    assert {"books", "temp", "voices"} <= declared


def test_runtime_directories_include_temp_books_and_voices(tmp_path):
    paths = _project_paths(tmp_path)
    paths.ensure_runtime_directories()
    for folder in (
        paths.books,
        paths.cache,
        paths.output,
        paths.projects,
        paths.logs,
        paths.models,
        paths.temp,
        paths.voices,
        paths.engine_manifests,
    ):
        assert folder.is_dir(), folder


def test_batch_jobs_support_old_callable_and_new_list_access():
    batch = BatchProcessor()
    assert isinstance(batch.jobs, JobCollection)
    assert callable(batch.jobs)

    batch.add(
        source="book.pdf",
        output="Output",
        voice="af_heart",
        speed=1.0,
        pitch=0.0,
        engine="kokoro",
    )
    assert len(batch.jobs) == 1
    assert len(batch.jobs()) == 1
    assert len(batch.all()) == 1


def test_cover_preview_failure_never_aborts_book_preview(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    import ui.preview_cover as preview_cover_module
    from ui.preview import PreviewPanel

    paths = _project_paths(tmp_path / "portable")
    paths.ensure_runtime_directories()
    monkeypatch.setattr(preview_cover_module, "PATHS", paths)

    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Chapter One\nA reliable preview test paragraph.")
    document.save(pdf_path)
    document.close()

    application = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.load_book(pdf_path)

    assert panel.current_book == pdf_path.resolve()
    assert "reliable preview" in panel.cleaned_text.lower()
    assert paths.temp.is_dir()
    assert panel.cover.last_error() == ""
    panel.deleteLater()
    application.processEvents()


def test_missing_cover_source_is_nonfatal(tmp_path, monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    import ui.preview_cover as preview_cover_module
    from ui.preview_cover import PreviewCover

    paths = _project_paths(tmp_path / "portable")
    paths.ensure_runtime_directories()
    monkeypatch.setattr(preview_cover_module, "PATHS", paths)

    application = QApplication.instance() or QApplication([])
    cover = PreviewCover()
    assert cover.load_cover(tmp_path / "missing.pdf") is False
    assert cover.text() == "No Cover"
    cover.deleteLater()
    application.processEvents()
