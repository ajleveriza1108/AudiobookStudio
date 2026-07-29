from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from core.config import Config
from core.library import Library
from core.ocr_corrections import find_correction_profile

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_r1177():
    source = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    assert 'R1.17.7' in source
    assert 'BUILD = 177' in source


def test_removed_book_is_not_restored_from_recent_history(tmp_path):
    book = tmp_path / "removed.pdf"
    book.write_bytes(b"%PDF-removed-book")
    defaults = tmp_path / "defaults.json"
    defaults.write_text("{}", encoding="utf-8")
    user = tmp_path / "config.local.json"

    config = Config(defaults_file=defaults, user_file=user)
    config.append_recent_book(book)
    assert config.recent_books() == [str(book.resolve())]

    config.remove_recent_book(book)
    assert config.recent_books() == []
    assert config.get("last_book") == ""
    assert config.is_book_removed(book) is True

    reloaded = Config(defaults_file=defaults, user_file=user)
    assert reloaded.recent_books() == []
    assert reloaded.get("last_book") == ""
    assert reloaded.is_book_removed(book) is True

    reloaded.append_recent_book(book)
    assert reloaded.recent_books() == [str(book.resolve())]
    assert reloaded.is_book_removed(book) is False


def test_library_updates_path_when_same_file_content_is_reselected(tmp_path):
    first = tmp_path / "old" / "book.pdf"
    second = tmp_path / "new" / "book.pdf"
    first.parent.mkdir()
    second.parent.mkdir()
    content = b"same complete selected PDF"
    first.write_bytes(content)
    second.write_bytes(content)

    database = tmp_path / "library.local.json"
    library = Library(database=database)
    assert library.add(first) is True
    assert library.add(second) is False

    entries = library.all()
    assert len(entries) == 1
    assert entries[0]["path"] == str(second.resolve())


def test_hardcoded_remember_when_profile_is_removed():
    assert not (ROOT / "Resources" / "OCRCorrections" / "remember_when_1945.json").exists()


def test_profiles_are_explicit_exact_hash_only(tmp_path, monkeypatch):
    source = tmp_path / "selected.pdf"
    source.write_bytes(b"complete selected source")
    profile_root = tmp_path / "Resources" / "OCRCorrections"
    profile_root.mkdir(parents=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    profile_file = profile_root / "profile.json"
    profile_file.write_text(
        json.dumps(
            {
                "schema": 1,
                "id": "test",
                "match": {"sha256": [digest], "page_count": 1},
                "pages": {"1": "wrong hardcoded text"},
            }
        ),
        encoding="utf-8",
    )

    import core.ocr_corrections as corrections
    monkeypatch.setattr(corrections, "PATHS", SimpleNamespace(project_root=tmp_path))
    assert find_correction_profile(source, page_count=1) is None

    data = json.loads(profile_file.read_text(encoding="utf-8"))
    data["automatic"] = True
    profile_file.write_text(json.dumps(data), encoding="utf-8")
    assert find_correction_profile(source, page_count=1) is not None

    data["match"]["sha256"] = ["0" * 64]
    profile_file.write_text(json.dumps(data), encoding="utf-8")
    assert find_correction_profile(source, page_count=1) is None


def test_selected_source_hash_flows_from_queue_to_project():
    controller = (ROOT / "controllers" / "generation_controller.py").read_text(encoding="utf-8")
    job = (ROOT / "core" / "job.py").read_text(encoding="utf-8")
    batch = (ROOT / "core" / "batch.py").read_text(encoding="utf-8")
    worker = (ROOT / "workers" / "generator_worker.py").read_text(encoding="utf-8")
    project = (ROOT / "core" / "project.py").read_text(encoding="utf-8")

    assert 'source_sha256 = content_sha256(source)' in controller
    assert '"source_sha256": source_sha256' in controller
    assert 'Queued exact selected source' in controller
    assert 'self.source_sha256' in job
    assert 'source_sha256=source_sha256' in batch
    assert 'expected_source_sha256=job.source_sha256' in worker
    assert 'f"{book.stem}__{selected_source_sha256[:12]}"' in project
    assert 'Selected Source.json' in project
    assert 'hardcoded_profile_allowed' in project


def test_ocr_cache_is_bound_to_complete_selected_file_hash():
    source = (ROOT / "core" / "ocr.py").read_text(encoding="utf-8")
    assert 'CACHE_SCHEMA = 9' in source
    assert 'LAYOUT_SCHEMA = 8' in source
    assert '"source_sha256": content_sha256(source)' in source
    assert 'different selected PDF fingerprint' in source


def test_remove_signal_clears_startup_history():
    sidebar = (ROOT / "ui" / "sidebar.py").read_text(encoding="utf-8")
    events = (ROOT / "ui" / "main_window_events.py").read_text(encoding="utf-8")
    manager = (ROOT / "ui" / "book_manager.py").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")

    assert 'book_removed = Signal(str)' in sidebar
    assert 'self.book_removed.emit(path)' in sidebar
    assert 'book_removed.connect(self.window.controller.books.removed)' in events
    assert 'remove_recent_book(path)' in manager
    assert 'not self.config.is_book_removed(last_book)' in app
    assert 'values["last_book"] = str(current_book) if current_book else ""' in app
