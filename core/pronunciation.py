from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
from threading import RLock
from typing import Any
from uuid import uuid4

from core.paths import PATHS


FILE = PATHS.project_root / "pronunciation.json"
SCHEMA_VERSION = 2


def _language_key(value: str) -> str:
    key = str(value or "all").strip().casefold().replace("_", "-")
    aliases = {
        "english": "en", "en-us": "en", "en-gb": "en",
        "tagalog": "tl", "filipino": "tl",
        "spanish": "es", "french": "fr", "german": "de",
        "italian": "it", "portuguese": "pt",
    }
    return aliases.get(key, key or "all")


class PronunciationDictionary:
    """Backward-compatible pronunciation rules with safe matching options."""

    def __init__(self, file: str | Path | None = None):
        self.file = Path(file or FILE)
        self.rules: list[dict[str, Any]] = []
        self._lock = RLock()
        self.load()

    @property
    def words(self) -> dict[str, str]:
        """Legacy dictionary view retained for older callers."""
        return {
            str(rule["source"]): str(rule["target"])
            for rule in self.rules
            if rule.get("enabled", True)
        }

    @staticmethod
    def _rule(source: str, target: str, **options: Any) -> dict[str, Any]:
        return {
            "id": str(options.get("id") or uuid4().hex),
            "source": str(source),
            "target": str(target),
            "enabled": bool(options.get("enabled", True)),
            "whole_word": bool(options.get("whole_word", True)),
            "case_sensitive": bool(options.get("case_sensitive", False)),
            "regex": bool(options.get("regex", False)),
            "language": str(options.get("language", "all") or "all"),
            "scope": str(options.get("scope", "global") or "global"),
            "notes": str(options.get("notes", "") or ""),
        }

    def load(self) -> None:
        with self._lock:
            if not self.file.is_file():
                self.rules = []
                self.save()
                return

            try:
                data = json.loads(self.file.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError, UnicodeError):
                data = {}

            rules: list[dict[str, Any]] = []
            if isinstance(data, dict) and isinstance(data.get("rules"), list):
                for item in data["rules"]:
                    if not isinstance(item, dict):
                        continue
                    source = str(item.get("source", ""))
                    target = str(item.get("target", ""))
                    if source:
                        options = {key: value for key, value in item.items() if key not in {"source", "target"}}
                        rules.append(self._rule(source, target, **options))
            elif isinstance(data, dict):
                # Migrate the original {"written": "spoken"} format.
                for source, target in data.items():
                    if str(source):
                        rules.append(
                            self._rule(
                                str(source),
                                str(target),
                                whole_word=False,
                                case_sensitive=True,
                            )
                        )
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("source"):
                        options = {key: value for key, value in item.items() if key not in {"source", "target"}}
                        rules.append(
                            self._rule(
                                str(item["source"]),
                                str(item.get("target", "")),
                                **options,
                            )
                        )

            self.rules = rules

    def save(self) -> None:
        with self._lock:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(self.file.suffix + ".tmp")
            data = {"schema": SCHEMA_VERSION, "rules": self.rules}
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.file)

    def list_rules(self) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self.rules)

    @staticmethod
    def _compiled(rule: dict[str, Any]) -> re.Pattern[str]:
        source = str(rule.get("source", ""))
        expression = source if rule.get("regex", False) else re.escape(source)
        if rule.get("whole_word", True) and not rule.get("regex", False):
            expression = rf"(?<!\w){expression}(?!\w)"
        flags = 0 if rule.get("case_sensitive", False) else re.IGNORECASE
        return re.compile(expression, flags)

    def replace(
        self,
        text: str,
        extra_rules: list[dict[str, Any]] | None = None,
        language: str = "all",
    ) -> str:
        value = str(text or "")
        combined = self.list_rules() + [dict(item) for item in (extra_rules or []) if isinstance(item, dict)]

        # The GUI may pass a snapshot of the same global rules already loaded
        # from pronunciation.json. De-duplicate those rules before applying
        # them so a replacement is never performed twice by accident.
        unique: dict[tuple[Any, ...], dict[str, Any]] = {}
        for rule in combined:
            identity = (
                str(rule.get("id", "")),
                str(rule.get("source", "")),
                str(rule.get("target", "")),
                bool(rule.get("whole_word", True)),
                bool(rule.get("case_sensitive", False)),
                bool(rule.get("regex", False)),
                _language_key(str(rule.get("language", "all"))),
                str(rule.get("scope", "global")),
            )
            unique[identity] = rule
        rules = list(unique.values())

        # Longer literal rules run first so abbreviations such as "St. John"
        # are not partially consumed by a shorter "St." rule.
        rules.sort(key=lambda item: len(str(item.get("source", ""))), reverse=True)

        for rule in rules:
            if not rule.get("enabled", True):
                continue
            rule_language = _language_key(str(rule.get("language", "all") or "all"))
            requested_language = _language_key(language)
            if requested_language != "all" and rule_language not in {"all", requested_language}:
                continue
            source = str(rule.get("source", ""))
            if not source:
                continue
            try:
                value = self._compiled(rule).sub(str(rule.get("target", "")), value)
            except re.error:
                # A broken optional regex rule must not stop book generation.
                continue
        return value

    def add(self, source: str, target: str, **options: Any) -> str:
        source = str(source).strip()
        if not source:
            raise ValueError("The written form cannot be empty.")
        rule = self._rule(source, str(target), **options)
        with self._lock:
            self.rules.append(rule)
            self.save()
        return str(rule["id"])

    def update(self, rule_id: str, **changes: Any) -> bool:
        with self._lock:
            for index, rule in enumerate(self.rules):
                if str(rule.get("id")) != str(rule_id):
                    continue
                updated = dict(rule)
                updated.update(changes)
                source = str(updated.get("source", "")).strip()
                if not source:
                    raise ValueError("The written form cannot be empty.")
                options = {key: value for key, value in updated.items() if key not in {"source", "target"}}
                self.rules[index] = self._rule(
                    source,
                    str(updated.get("target", "")),
                    **options,
                )
                self.save()
                return True
        return False

    def remove(self, rule_id: str) -> bool:
        with self._lock:
            before = len(self.rules)
            self.rules = [rule for rule in self.rules if str(rule.get("id")) != str(rule_id)]
            changed = len(self.rules) != before
            if changed:
                self.save()
            return changed

    def clear(self) -> None:
        with self._lock:
            self.rules = []
            self.save()

    def preview(self, text: str, rule: dict[str, Any] | None = None) -> str:
        if rule is None:
            return self.replace(text)
        temporary = PronunciationDictionary.__new__(PronunciationDictionary)
        temporary.file = self.file
        temporary.rules = []
        temporary._lock = RLock()
        return temporary.replace(text, [rule])
