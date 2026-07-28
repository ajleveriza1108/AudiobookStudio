from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.paths import PATHS


@dataclass(frozen=True)
class OCRCorrectionProfile:
    profile_id: str
    description: str
    pages: dict[int, str]
    source: Path

    def page_text(self, page_number: int) -> str | None:
        value = self.pages.get(int(page_number))
        value = str(value or "").strip()
        return value or None


def content_sha256(path: str | Path) -> str:
    source = Path(path).expanduser().resolve()
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalized_filename(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", " ", path.stem.casefold()).strip()


def _load_profile(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def find_correction_profile(
    source: str | Path,
    *,
    page_count: int,
) -> OCRCorrectionProfile | None:
    """Return a verified narration profile for a known scanned edition.

    Exact SHA-256 matching is preferred. A conservative fallback requires the
    exact byte size, page count, and all filename tokens declared by the
    profile. This prevents a similarly named but different book from receiving
    another edition's text.
    """

    source_path = Path(source).expanduser().resolve()
    profile_root = PATHS.project_root / "Resources" / "OCRCorrections"
    if not profile_root.is_dir():
        return None

    try:
        stat = source_path.stat()
        digest = content_sha256(source_path)
    except OSError:
        return None

    filename = _normalized_filename(source_path)
    for profile_file in sorted(profile_root.glob("*.json")):
        data = _load_profile(profile_file)
        if not data or int(data.get("schema") or 0) != 1:
            continue
        match = data.get("match") if isinstance(data.get("match"), dict) else {}
        hashes = {str(value).casefold() for value in (match.get("sha256") or [])}
        exact_hash = digest.casefold() in hashes

        fallback = (
            int(match.get("size_bytes") or -1) == int(stat.st_size)
            and int(match.get("page_count") or -1) == int(page_count)
        )
        tokens = [str(value).casefold().strip() for value in (match.get("filename_contains") or [])]
        if tokens:
            fallback = fallback and all(token in filename for token in tokens)

        if not exact_hash and not fallback:
            continue

        raw_pages = data.get("pages") if isinstance(data.get("pages"), dict) else {}
        pages: dict[int, str] = {}
        for key, value in raw_pages.items():
            try:
                number = int(key)
            except (TypeError, ValueError):
                continue
            text = str(value or "").strip()
            if number > 0 and text:
                pages[number] = text
        if not pages:
            continue
        return OCRCorrectionProfile(
            profile_id=str(data.get("id") or profile_file.stem),
            description=str(data.get("description") or "Verified OCR correction profile"),
            pages=pages,
            source=profile_file,
        )
    return None
