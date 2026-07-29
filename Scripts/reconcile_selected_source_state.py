from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.is_file():
        return fallback
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, json.JSONDecodeError):
        return fallback
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _resolved(value: str | Path) -> str:
    return str(Path(value).expanduser().resolve())


def _key(value: str | Path) -> str:
    return os.path.normcase(_resolved(value))


def reconcile(project_root: Path, backup_root: Path | None = None) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    config_path = project_root / "config.local.json"
    library_path = project_root / "library.local.json"

    config = _read_json(config_path, {})
    if not isinstance(config, dict):
        config = {}
    library = _read_json(library_path, [])
    if not isinstance(library, list):
        library = []

    if backup_root is not None:
        backup_root = backup_root.expanduser().resolve()
        backup_root.mkdir(parents=True, exist_ok=True)
        for path in (config_path, library_path):
            if path.is_file():
                shutil.copy2(path, backup_root / path.name)

    library_paths: list[str] = []
    for item in library:
        if not isinstance(item, dict):
            continue
        value = str(item.get("path") or "").strip()
        if value:
            try:
                library_paths.append(_resolved(value))
            except (OSError, RuntimeError, ValueError):
                continue
    library_keys = {_key(path) for path in library_paths}

    removed: list[str] = []
    removed_keys: set[str] = set()
    for value in config.get("removed_books", []) or []:
        if not isinstance(value, (str, Path)) or not str(value).strip():
            continue
        try:
            path = _resolved(value)
        except (OSError, RuntimeError, ValueError):
            continue
        key = _key(path)
        if key not in removed_keys:
            removed.append(path)
            removed_keys.add(key)

    recent: list[str] = []
    recent_keys: set[str] = set()
    reconciled_removed = 0
    for value in config.get("last_books", []) or []:
        if not isinstance(value, (str, Path)) or not str(value).strip():
            continue
        try:
            path = _resolved(value)
        except (OSError, RuntimeError, ValueError):
            continue
        key = _key(path)
        if key in library_keys:
            if key not in recent_keys and key not in removed_keys:
                recent.append(path)
                recent_keys.add(key)
        else:
            if key not in removed_keys:
                removed.insert(0, path)
                removed_keys.add(key)
            reconciled_removed += 1

    last_book = str(config.get("last_book") or "").strip()
    if last_book:
        try:
            last_book = _resolved(last_book)
            key = _key(last_book)
        except (OSError, RuntimeError, ValueError):
            key = ""
            last_book = ""
        if not key or key not in library_keys or key in removed_keys:
            if key and key not in removed_keys:
                removed.insert(0, last_book)
                removed_keys.add(key)
            last_book = ""
            reconciled_removed += 1

    config["last_books"] = recent[:20]
    config["last_book"] = last_book
    config["removed_books"] = removed[:200]
    _atomic_json(config_path, config)

    quarantined: list[str] = []
    ocr_root = project_root / "Cache" / "OCR"
    quarantine_root = (
        backup_root / "stale_ocr_cache"
        if backup_root is not None
        else project_root / "Cache" / "OCR-Stale-R1.17.7"
    )
    if ocr_root.is_dir():
        for folder in sorted(path for path in ocr_root.iterdir() if path.is_dir()):
            manifest = _read_json(folder / "manifest.json", {})
            if not isinstance(manifest, dict):
                continue
            profile = str(manifest.get("correction_profile") or "").casefold()
            schema = int(manifest.get("schema") or 0)
            has_wrong_profile = "remember_when_1945" in profile
            if not has_wrong_profile and schema >= 7:
                continue
            # Schema 7 invalidates old caches. Quarantine only the known title-
            # override cache; other old caches are safely ignored and rebuilt.
            if not has_wrong_profile:
                continue
            quarantine_root.mkdir(parents=True, exist_ok=True)
            target = quarantine_root / folder.name
            if target.exists():
                shutil.rmtree(target)
            shutil.move(str(folder), str(target))
            quarantined.append(str(target))

    return {
        "config_path": str(config_path),
        "library_entries": len(library_paths),
        "recent_books": len(recent),
        "removed_history_entries": reconciled_removed,
        "quarantined_ocr_caches": quarantined,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--backup-root", default="")
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    result = reconcile(
        Path(args.project_root),
        Path(args.backup_root) if args.backup_root else None,
    )
    if args.report:
        _atomic_json(Path(args.report), result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
