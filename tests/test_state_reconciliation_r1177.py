from __future__ import annotations

import json
from pathlib import Path

from Scripts.reconcile_selected_source_state import reconcile


def test_reconcile_removes_startup_history_not_in_library(tmp_path):
    kept = tmp_path / "kept.pdf"
    removed = tmp_path / "removed.pdf"
    kept.write_bytes(b"kept")
    removed.write_bytes(b"removed")
    (tmp_path / "library.local.json").write_text(
        json.dumps([{"title": "kept", "path": str(kept.resolve())}]),
        encoding="utf-8",
    )
    (tmp_path / "config.local.json").write_text(
        json.dumps(
            {
                "last_book": str(removed.resolve()),
                "last_books": [str(removed.resolve()), str(kept.resolve())],
                "removed_books": [],
            }
        ),
        encoding="utf-8",
    )

    result = reconcile(tmp_path)
    config = json.loads((tmp_path / "config.local.json").read_text(encoding="utf-8"))
    assert config["last_book"] == ""
    assert config["last_books"] == [str(kept.resolve())]
    assert str(removed.resolve()) in config["removed_books"]
    assert result["removed_history_entries"] >= 1


def test_reconcile_quarantines_known_hardcoded_profile_cache(tmp_path):
    cache = tmp_path / "Cache" / "OCR" / "abc"
    cache.mkdir(parents=True)
    (cache / "manifest.json").write_text(
        json.dumps({"schema": 6, "correction_profile": "remember_when_1945_verified"}),
        encoding="utf-8",
    )
    (tmp_path / "library.local.json").write_text("[]", encoding="utf-8")
    backup = tmp_path / "backup"

    result = reconcile(tmp_path, backup)
    assert not cache.exists()
    assert (backup / "stale_ocr_cache" / "abc" / "manifest.json").is_file()
    assert len(result["quarantined_ocr_caches"]) == 1
