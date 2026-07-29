from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import core.ocr_corrections as corrections

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "Resources" / "OCRCorrections" / "1945_remember_when_authoritative_exact_v1.json"
EXPECTED_SHA = "423ec901a554733ffcabfba0bcd265cee312227b255eb7a252e2af966874acac"


def test_authoritative_profile_is_exact_hash_only_and_complete():
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["automatic"] is True
    assert data["match"] == {"sha256": [EXPECTED_SHA], "page_count": 10}
    assert set(data["pages"]) == {str(number) for number in range(1, 11)}
    assert data["pages"]["1"].startswith("1945. Remember When.")
    assert data["pages"]["2"].startswith("Remember When, 1945. To Dad.")
    assert data["pages"]["4"].startswith("1945 World News.")
    assert data["pages"]["5"].startswith("1945 National News.")
    assert data["pages"]["8"].startswith("1945 Birth Notices.")
    assert data["pages"]["9"].startswith("1945 Sports News.")
    assert data["pages"]["10"].startswith("1945 Music and Movie Favorites.")
    assert "World Series champion: Detroit Tigers." in data["pages"]["9"]
    assert "Accentuate the Positive" in data["pages"]["10"]


def test_exact_source_uses_authoritative_pages(monkeypatch, tmp_path):
    source = tmp_path / "1945 Remember When.pdf"
    source.write_bytes(b"test fixture; content hash is patched")
    monkeypatch.setattr(corrections, "PATHS", SimpleNamespace(project_root=ROOT))
    monkeypatch.setattr(corrections, "content_sha256", lambda _path: EXPECTED_SHA)
    profile = corrections.find_correction_profile(source, page_count=10)
    assert profile is not None
    assert profile.profile_id == "remember_when_1945_authoritative_exact_v1"
    assert profile.page_text(9).startswith("1945 Sports News.")
    assert profile.page_text(10).startswith("1945 Music and Movie Favorites.")


def test_other_source_never_receives_authoritative_pages(monkeypatch, tmp_path):
    source = tmp_path / "different.pdf"
    source.write_bytes(b"different source")
    monkeypatch.setattr(corrections, "PATHS", SimpleNamespace(project_root=ROOT))
    monkeypatch.setattr(corrections, "content_sha256", lambda _path: "0" * 64)
    assert corrections.find_correction_profile(source, page_count=10) is None
    monkeypatch.setattr(corrections, "content_sha256", lambda _path: EXPECTED_SHA)
    assert corrections.find_correction_profile(source, page_count=9) is None
