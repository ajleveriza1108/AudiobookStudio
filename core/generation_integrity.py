from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import wave
from typing import Any

from core.chunk_validator import ChunkValidator


INTEGRITY_SCHEMA = 1
_WORD = re.compile(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*")


class GenerationIntegrityError(RuntimeError):
    """Raised before a partial or internally inconsistent audiobook can replace a good file."""

    def __init__(self, message: str, report: dict[str, Any] | None = None):
        super().__init__(message)
        self.report = dict(report or {})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _word_count(value: str) -> int:
    return len(_WORD.findall(str(value or "")))


def _pages(value: str) -> list[str]:
    text = str(value or "").replace("\r", "")
    if "\f" in text:
        return text.split("\f")
    return [text]


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def save_report(project: str | Path, report: dict[str, Any]) -> tuple[Path, Path]:
    root = Path(project)
    report = dict(report)
    report.setdefault("schema", INTEGRITY_SCHEMA)
    report["updated"] = _now()

    json_path = root / "generation_integrity_report.json"
    text_path = root / "Generation Integrity Report.txt"
    _atomic_json(json_path, report)

    lines = [
        "AUDIOBOOK STUDIO - GENERATION INTEGRITY REPORT",
        "=" * 72,
        f"Status: {str(report.get('status', 'unknown')).upper()}",
        f"Source pages: {report.get('source_pages', 0)}",
        f"Extracted pages: {report.get('extracted_pages', 0)}",
        f"Substantive extracted pages: {report.get('substantive_pages', 0)}",
        f"Raw extracted words: {report.get('raw_words', 0)}",
        f"Cleaned words: {report.get('cleaned_words', 0)}",
        f"Narration words: {report.get('narration_words', 0)}",
        f"Narration sections: {report.get('chunks', 0)}",
        f"Detected chapters/sections: {report.get('chapters', 0)}",
        "",
    ]

    failures = list(report.get("failures") or [])
    warnings = list(report.get("warnings") or [])
    if failures:
        lines.append("BLOCKING FAILURES")
        lines.append("-" * 72)
        lines.extend(f"- {item}" for item in failures)
        lines.append("")
    if warnings:
        lines.append("WARNINGS")
        lines.append("-" * 72)
        lines.extend(f"- {item}" for item in warnings)
        lines.append("")
    if not failures and not warnings:
        lines.append("No completeness or assembly problems were detected.")
        lines.append("")

    if report.get("chunk_validation"):
        chunk = report["chunk_validation"]
        lines.extend(
            [
                "CHUNK VALIDATION",
                "-" * 72,
                f"Expected: {chunk.get('expected', 0)}",
                f"Found: {chunk.get('found', 0)}",
                f"Missing: {', '.join(str(x) for x in chunk.get('missing', [])) or 'None'}",
                f"Unexpected: {', '.join(str(x) for x in chunk.get('unexpected', [])) or 'None'}",
                "",
            ]
        )

    if report.get("audio_validation"):
        audio = report["audio_validation"]
        lines.extend(
            [
                "FINAL AUDIO VALIDATION",
                "-" * 72,
                f"Expected frames: {audio.get('expected_frames', 0)}",
                f"Actual frames: {audio.get('actual_frames', 0)}",
                f"Duration: {audio.get('duration_seconds', 0):.2f} seconds",
                f"Estimated speaking rate: {audio.get('estimated_wpm', 0):.1f} words per minute",
                "",
            ]
        )

    _atomic_text(text_path, "\n".join(lines).rstrip() + "\n")
    return json_path, text_path


def build_pre_generation_report(
    *,
    source: str | Path,
    raw_text: str,
    cleaned_text: str,
    narration_text: str,
    chunks: list[str],
    chapters: list[dict[str, Any]],
    chapter_plan: list[dict[str, Any]] | None,
    metadata: dict[str, Any] | None,
    diagnostics: dict[str, Any] | None,
) -> dict[str, Any]:
    source_path = Path(source)
    meta = dict(metadata or {})
    diag = dict(diagnostics or {})

    source_pages = _safe_int(meta.get("pages"), 0)
    extracted_pages = _safe_int(diag.get("pages"), 0)
    raw_pages = _pages(raw_text)
    if extracted_pages <= 0:
        extracted_pages = len(raw_pages)

    raw_page_words = [_word_count(page) for page in raw_pages]
    substantive_pages = sum(1 for count in raw_page_words if count >= 4)
    raw_words = sum(raw_page_words)
    cleaned_words = _word_count(cleaned_text)
    narration_words = _word_count(narration_text)
    narration_characters = len(str(narration_text or ""))

    exclusions = [
        item for item in (chapter_plan or [])
        if isinstance(item, dict) and item.get("included") is False
    ]
    explicit_exclusions = len(exclusions)

    failures: list[str] = []
    warnings: list[str] = []

    is_pdf = source_path.suffix.casefold() == ".pdf"
    ocr_used = bool(diag.get("ocr_used"))
    if is_pdf and source_pages > 0:
        if extracted_pages != source_pages:
            failures.append(
                f"The source contains {source_pages} pages, but the extracted text records "
                f"only {extracted_pages}. The OCR cache or extraction is incomplete."
            )
        if len(raw_pages) != source_pages:
            failures.append(
                f"The extracted text contains {len(raw_pages)} page segment(s), but the PDF "
                f"contains {source_pages}. Full-book generation is blocked."
            )

        accounted = _safe_int(diag.get("ocr_pages"), 0) + _safe_int(
            diag.get("readable_pages"), 0
        )
        if ocr_used and accounted and accounted != source_pages:
            failures.append(
                f"OCR accounts for {accounted} of {source_pages} pages. The missing pages "
                "must be reprocessed before narration."
            )

        if source_pages >= 4 and substantive_pages < math.ceil(source_pages * 0.5):
            failures.append(
                f"Only {substantive_pages} of {source_pages} pages contain substantive "
                "extracted text. This strongly indicates a partial OCR result."
            )

    raw_retention = narration_words / max(1, raw_words)
    cleaned_retention = narration_words / max(1, cleaned_words)

    # Automatic full-book generation must never silently retain only the beginning
    # of a scanned book. Explicitly excluded chapters are treated as intentional.
    if explicit_exclusions == 0:
        if raw_words >= 100 and raw_retention < 0.40:
            failures.append(
                f"Narration retains only {raw_retention:.0%} of the extracted words. "
                "The book appears truncated or over-cleaned."
            )
        if cleaned_words >= 100 and cleaned_retention < 0.70:
            failures.append(
                f"Narration retains only {cleaned_retention:.0%} of the cleaned book text. "
                "Unselected or dropped sections were detected."
            )
    else:
        warnings.append(
            f"{explicit_exclusions} chapter/section exclusion(s) were selected by the user."
        )

    if narration_words < 5:
        failures.append("Too little narration text remains to generate an audiobook.")
    if not chunks:
        failures.append("No narration sections were created.")
    if chapters and narration_words:
        chapter_words = sum(_safe_int(item.get("word_count"), 0) for item in chapters)
        if chapter_words and abs(chapter_words - narration_words) > max(12, narration_words * 0.08):
            failures.append(
                "The chapter map does not account for the complete narration text."
            )

    if any(not str(chunk or "").strip() for chunk in chunks):
        failures.append("One or more narration sections are empty.")

    expected_min_chunks = max(1, math.ceil(narration_characters / 1400))
    if len(chunks) < expected_min_chunks:
        failures.append(
            f"The narration requires at least {expected_min_chunks} section(s) at the "
            f"stable maximum size, but only {len(chunks)} were produced."
        )

    if raw_words >= 100 and raw_retention < 0.55 and not failures:
        warnings.append(
            f"Narration word retention is {raw_retention:.0%}; review the text before release."
        )

    return {
        "schema": INTEGRITY_SCHEMA,
        "stage": "pre-generation",
        "status": "blocked" if failures else "passed",
        "source": str(source_path),
        "source_pages": source_pages,
        "extracted_pages": extracted_pages,
        "raw_page_segments": len(raw_pages),
        "substantive_pages": substantive_pages,
        "raw_page_word_counts": raw_page_words,
        "raw_words": raw_words,
        "cleaned_words": cleaned_words,
        "narration_words": narration_words,
        "narration_characters": narration_characters,
        "raw_retention": round(raw_retention, 4),
        "cleaned_retention": round(cleaned_retention, 4),
        "chunks": len(chunks),
        "chapters": len(chapters),
        "explicit_exclusions": explicit_exclusions,
        "ocr_used": ocr_used,
        "ocr_backend": str(diag.get("ocr_backend") or ""),
        "ocr_cache_hit": bool(diag.get("ocr_cache_hit")),
        "narration_sha256": hashlib.sha256(
            str(narration_text or "").encode("utf-8")
        ).hexdigest(),
        "failures": failures,
        "warnings": warnings,
    }


def require_pre_generation_integrity(project: str | Path, **kwargs: Any) -> dict[str, Any]:
    report = build_pre_generation_report(**kwargs)
    save_report(project, report)
    failures = list(report.get("failures") or [])
    if failures:
        raise GenerationIntegrityError(
            "Full-book generation was blocked because the extracted or selected text "
            "is incomplete. See Generation Integrity Report.txt.",
            report,
        )
    return report


def validate_chunk_set(folder: str | Path, expected_total: int) -> dict[str, Any]:
    root = Path(folder)
    expected_total = max(0, int(expected_total))
    files = ChunkValidator.ordered(root)
    numbers = [ChunkValidator.number(path) for path in files]
    numbers = [int(number) for number in numbers if number is not None]
    expected = set(range(1, expected_total + 1))
    actual = set(numbers)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    invalid = [path.name for path in files if not ChunkValidator.valid(path)]
    duplicate_numbers = sorted(
        number for number in actual if numbers.count(number) > 1
    )
    failures: list[str] = []
    if len(files) != expected_total:
        failures.append(
            f"Expected {expected_total} narration sections but found {len(files)}."
        )
    if missing:
        failures.append(f"Missing narration section numbers: {missing}.")
    if unexpected:
        failures.append(f"Unexpected narration section numbers: {unexpected}.")
    if duplicate_numbers:
        failures.append(f"Duplicate narration section numbers: {duplicate_numbers}.")
    if invalid:
        failures.append(f"Damaged narration section files: {invalid}.")

    return {
        "status": "blocked" if failures else "passed",
        "expected": expected_total,
        "found": len(files),
        "numbers": numbers,
        "missing": missing,
        "unexpected": unexpected,
        "duplicates": duplicate_numbers,
        "invalid": invalid,
        "files": [path.name for path in files],
        "failures": failures,
    }


def require_chunk_integrity(
    project: str | Path,
    expected_total: int,
    base_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = dict(base_report or {})
    chunk_report = validate_chunk_set(project, expected_total)
    report["stage"] = "generated-chunks"
    report["chunk_validation"] = chunk_report
    report["failures"] = list(report.get("failures") or []) + list(
        chunk_report.get("failures") or []
    )
    report["status"] = "blocked" if report["failures"] else "passed"
    save_report(project, report)
    if chunk_report["failures"]:
        raise GenerationIntegrityError(
            "Narration sections are incomplete or inconsistent. The existing audiobook "
            "was not replaced.",
            report,
        )
    return report


def validate_merged_wav(
    *,
    candidate: str | Path,
    chunk_folder: str | Path,
    expected_total: int,
    narration_words: int,
    speed: float,
) -> dict[str, Any]:
    candidate_path = Path(candidate)
    chunks = ChunkValidator.ordered(chunk_folder)
    if len(chunks) != int(expected_total):
        return {
            "status": "blocked",
            "failures": [
                f"Expected {int(expected_total)} chunks before audio validation, "
                f"but found {len(chunks)}."
            ],
        }

    expected_frames = 0
    sample_rate = 0
    parameters: tuple[int, int, int, str] | None = None
    failures: list[str] = []
    for path in chunks:
        details = ChunkValidator.inspect(path)
        if not details["valid"]:
            failures.append(f"Invalid chunk: {path.name}.")
            continue
        current = (
            int(details["channels"]),
            int(details["sample_width"]),
            int(details["sample_rate"]),
            "NONE",
        )
        if parameters is None:
            parameters = current
            sample_rate = int(details["sample_rate"])
        elif current[:3] != parameters[:3]:
            failures.append(f"Chunk format mismatch: {path.name}.")
        expected_frames += int(details["frames"])

    actual_frames = 0
    actual_rate = 0
    try:
        with wave.open(str(candidate_path), "rb") as wav:
            actual_frames = int(wav.getnframes())
            actual_rate = int(wav.getframerate())
    except (OSError, wave.Error):
        failures.append("The assembled candidate WAV is missing or unreadable.")

    if sample_rate and actual_rate and sample_rate != actual_rate:
        failures.append(
            f"The candidate sample rate is {actual_rate}, expected {sample_rate}."
        )
    if expected_frames and actual_frames != expected_frames:
        failures.append(
            f"The candidate contains {actual_frames} frames, but the complete chunk set "
            f"contains {expected_frames}. The WAV is incomplete."
        )

    duration = actual_frames / max(1, actual_rate)
    estimated_wpm = (float(narration_words) / max(duration, 0.001)) * 60.0
    adjusted_speed = max(0.5, min(2.0, float(speed or 1.0)))
    minimum_wpm = 70.0 * adjusted_speed
    maximum_wpm = 280.0 * adjusted_speed
    if narration_words >= 100 and not (minimum_wpm <= estimated_wpm <= maximum_wpm):
        failures.append(
            f"The final duration implies {estimated_wpm:.1f} words per minute, outside "
            "the safe completeness range."
        )

    return {
        "status": "blocked" if failures else "passed",
        "expected_frames": expected_frames,
        "actual_frames": actual_frames,
        "sample_rate": actual_rate,
        "duration_seconds": round(duration, 4),
        "narration_words": int(narration_words),
        "estimated_wpm": round(estimated_wpm, 3),
        "failures": failures,
    }


def require_merged_audio_integrity(
    project: str | Path,
    *,
    candidate: str | Path,
    chunk_folder: str | Path,
    expected_total: int,
    narration_words: int,
    speed: float,
    base_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = dict(base_report or {})
    audio_report = validate_merged_wav(
        candidate=candidate,
        chunk_folder=chunk_folder,
        expected_total=expected_total,
        narration_words=narration_words,
        speed=speed,
    )
    report["stage"] = "assembled-audio"
    report["audio_validation"] = audio_report
    report["failures"] = list(report.get("failures") or []) + list(
        audio_report.get("failures") or []
    )
    report["status"] = "blocked" if report["failures"] else "passed"
    save_report(project, report)
    if audio_report["failures"]:
        Path(candidate).unlink(missing_ok=True)
        raise GenerationIntegrityError(
            "The assembled WAV failed the completeness check. The previous audiobook "
            "was preserved.",
            report,
        )
    return report


def promote_candidate(
    candidate: str | Path,
    final: str | Path,
    *,
    keep_previous: int = 5,
) -> Path | None:
    candidate_path = Path(candidate)
    final_path = Path(final)
    if not candidate_path.is_file():
        raise GenerationIntegrityError("The verified candidate WAV is missing.")

    previous: Path | None = None
    if final_path.is_file():
        history = final_path.parent / "Previous Audio"
        history.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        previous = history / f"{final_path.stem}_before_{stamp}{final_path.suffix}"
        shutil.copy2(final_path, previous)

        existing = sorted(
            history.glob(f"{final_path.stem}_before_*{final_path.suffix}"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for old in existing[max(1, int(keep_previous)):]:
            old.unlink(missing_ok=True)

    final_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(candidate_path, final_path)
    return previous
