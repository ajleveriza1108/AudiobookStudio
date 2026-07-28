from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import fitz
import numpy as np

from core.ocr_corrections import find_correction_profile
from core.ocr_layout import (
    OCRLayoutResult,
    OCRRegion,
    layout_ocr_regions,
    regions_from_rapidocr,
    regions_from_tesseract_tsv,
)
from core.paths import PATHS


class OCRUnavailableError(RuntimeError):
    """Raised when a scanned document needs OCR but no local engine is ready."""


class OCRProcessingError(RuntimeError):
    """Raised when OCR ran but did not produce usable narration text."""


ProgressCallback = Callable[[int, int, str], None]
CancelCallback = Callable[[], bool]
LogCallback = Callable[[str], None]


@dataclass(frozen=True)
class OCRAvailability:
    available: bool
    backend: str
    detail: str


@dataclass(frozen=True)
class OCRTextResult:
    text: str
    backend: str
    pages: int
    ocr_pages: int
    embedded_pages: int
    cache_hit: bool
    cache_folder: Path
    structured_pages: int = 0
    timeline_pages: int = 0
    multi_column_pages: int = 0
    low_confidence_pages: int = 0
    layout_schema: int = 0
    correction_profile: str = ""


@dataclass(frozen=True)
class OCRPageRecognition:
    text: str
    mode: str = "standard"
    confidence: float = 1.0
    regions: tuple[OCRRegion, ...] = ()
    reading_order: tuple[int, ...] = ()
    warnings: tuple[str, ...] = ()
    details: dict[str, Any] | None = None

    @classmethod
    def from_layout(cls, result: OCRLayoutResult) -> "OCRPageRecognition":
        return cls(
            text=result.text,
            mode=result.mode,
            confidence=result.confidence,
            regions=result.regions,
            reading_order=result.reading_order,
            warnings=result.warnings,
            details=result.details,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "confidence": round(float(self.confidence), 4),
            "text": self.text,
            "reading_order": list(self.reading_order),
            "warnings": list(self.warnings),
            "details": dict(self.details or {}),
            "regions": [region.to_dict() for region in self.regions],
        }


class OCRService:
    """Offline OCR for scanned and mixed PDFs with coordinate-aware reading order.

    RapidOCR + ONNX Runtime is preferred. Tesseract remains a local fallback.
    R1.14 retains OCR bounding boxes, detects timeline/month grids, and reads
    each cell as a unit instead of flattening unrelated columns across a row.
    """

    MIN_EMBEDDED_CHARACTERS = 24
    MIN_RESULT_WORDS = 5
    DEFAULT_DPI = 220
    CACHE_SCHEMA = 3
    LAYOUT_SCHEMA = 2
    LOW_LAYOUT_CONFIDENCE = 0.68
    _rapid_engine: Any = None

    @classmethod
    def availability(cls) -> OCRAvailability:
        if importlib.util.find_spec("rapidocr") and importlib.util.find_spec("onnxruntime"):
            return OCRAvailability(
                True,
                "RapidOCR",
                "Offline RapidOCR and ONNX Runtime are installed.",
            )

        executable = cls._find_tesseract()
        if executable:
            return OCRAvailability(
                True,
                "Tesseract",
                f"Local Tesseract OCR found at {executable}.",
            )

        return OCRAvailability(
            False,
            "Unavailable",
            "Offline OCR is not installed. Run install_dependencies.ps1.",
        )

    @classmethod
    def is_available(cls) -> bool:
        return cls.availability().available

    @classmethod
    def _find_tesseract(cls) -> Path | None:
        candidates: list[Path] = [PATHS.project_root / "Tools" / "Tesseract" / "tesseract.exe"]

        found = shutil.which("tesseract")
        if found:
            candidates.append(Path(found))

        for environment_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            base = os.getenv(environment_name, "").strip()
            if base:
                candidates.extend(
                    [
                        Path(base) / "Tesseract-OCR" / "tesseract.exe",
                        Path(base) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
                    ]
                )

        for candidate in candidates:
            try:
                if candidate.is_file():
                    return candidate.resolve()
            except OSError:
                continue
        return None

    @staticmethod
    def _source_fingerprint(path: Path) -> str:
        stat = path.stat()
        digest = hashlib.sha256()
        digest.update(str(path.resolve()).casefold().encode("utf-8", errors="ignore"))
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(str(stat.st_mtime_ns).encode("ascii"))

        with path.open("rb") as stream:
            first = stream.read(1024 * 1024)
            digest.update(first)
            if stat.st_size > 1024 * 1024:
                stream.seek(max(0, stat.st_size - 1024 * 1024))
                digest.update(stream.read(1024 * 1024))
        return digest.hexdigest()

    @classmethod
    def cache_folder(cls, path: str | Path) -> Path:
        source = Path(path).expanduser().resolve()
        return PATHS.cache / "OCR" / cls._source_fingerprint(source)

    @classmethod
    def _read_manifest(cls, folder: Path) -> dict[str, Any] | None:
        manifest_file = folder / "manifest.json"
        if not manifest_file.is_file():
            return None
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        if int(manifest.get("schema") or 0) != cls.CACHE_SCHEMA:
            return None
        if int(manifest.get("layout_schema") or 0) != cls.LAYOUT_SCHEMA:
            return None
        return manifest

    @classmethod
    def cached_text(cls, path: str | Path) -> OCRTextResult | None:
        source = Path(path).expanduser().resolve()
        try:
            folder = cls.cache_folder(source)
        except OSError:
            return None

        text_file = folder / "ocr_text.txt"
        manifest = cls._read_manifest(folder)
        if not text_file.is_file() or manifest is None:
            # R1.14 deliberately rejects pre-layout caches. They were created by
            # flattening OCR lines and can contain incorrect cross-column order.
            return None

        try:
            text = text_file.read_text(encoding="utf-8-sig")
        except OSError:
            return None

        if len(text.split()) < cls.MIN_RESULT_WORDS:
            return None

        return OCRTextResult(
            text=text,
            backend=str(manifest.get("backend") or "Cached OCR"),
            pages=int(manifest.get("pages") or 0),
            ocr_pages=int(manifest.get("ocr_pages") or 0),
            embedded_pages=int(manifest.get("embedded_pages") or 0),
            cache_hit=True,
            cache_folder=folder,
            structured_pages=int(manifest.get("structured_pages") or 0),
            timeline_pages=int(manifest.get("timeline_pages") or 0),
            multi_column_pages=int(manifest.get("multi_column_pages") or 0),
            low_confidence_pages=int(manifest.get("low_confidence_pages") or 0),
            layout_schema=int(manifest.get("layout_schema") or 0),
            correction_profile=str(manifest.get("correction_profile") or ""),
        )

    @classmethod
    def _rapidocr_engine(cls):
        if cls._rapid_engine is None:
            from rapidocr import RapidOCR

            cls._rapid_engine = RapidOCR()
        return cls._rapid_engine

    @classmethod
    def _recognize_rapidocr(cls, pixmap: fitz.Pixmap) -> OCRPageRecognition:
        image = np.frombuffer(pixmap.samples, dtype=np.uint8)
        image = image.reshape(pixmap.height, pixmap.width, pixmap.n)
        if pixmap.n > 3:
            image = image[:, :, :3]
        result = cls._rapidocr_engine()(image)
        regions = regions_from_rapidocr(result)
        if regions:
            layout = layout_ocr_regions(
                regions,
                page_width=float(pixmap.width),
                page_height=float(pixmap.height),
            )
            return OCRPageRecognition.from_layout(layout)

        # Compatibility fallback for adapters that expose text but not boxes.
        texts = getattr(result, "txts", None)
        if texts is None and isinstance(result, dict):
            texts = result.get("txts") or result.get("texts")
        if isinstance(result, tuple) and result:
            result = result[0]
        if texts is None and isinstance(result, (list, tuple)):
            values: list[str] = []
            for item in result:
                if isinstance(item, (list, tuple)) and len(item) >= 2 and isinstance(item[1], str):
                    values.append(item[1])
                elif isinstance(item, dict) and (item.get("text") or item.get("txt")):
                    values.append(str(item.get("text") or item.get("txt")))
            texts = values
        text = "\n".join(str(value).strip() for value in (texts or []) if str(value).strip()).strip()
        return OCRPageRecognition(
            text=text,
            mode="unstructured-fallback",
            confidence=0.45 if text else 0.0,
            warnings=("OCR text did not include bounding boxes; reading order needs review.",),
        )

    @classmethod
    def _recognize_tesseract(
        cls, pixmap: fitz.Pixmap, language: str
    ) -> OCRPageRecognition:
        executable = cls._find_tesseract()
        if executable is None:
            raise OCRUnavailableError("Tesseract OCR was not found.")

        PATHS.temp.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="audiobookstudio_ocr_", dir=PATHS.temp) as folder:
            image_path = Path(folder) / "page.png"
            pixmap.save(image_path)
            command = [
                str(executable),
                str(image_path),
                "stdout",
                "-l",
                language or "eng",
                "--psm",
                "11",
                "tsv",
            ]
            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or "Tesseract OCR failed."
                raise OCRProcessingError(detail)
            regions = regions_from_tesseract_tsv(completed.stdout)
            layout = layout_ocr_regions(
                regions,
                page_width=float(pixmap.width),
                page_height=float(pixmap.height),
            )
            return OCRPageRecognition.from_layout(layout)

    @classmethod
    def _recognize_page(
        cls, pixmap: fitz.Pixmap, backend: str, language: str
    ) -> OCRPageRecognition | str:
        if backend == "RapidOCR":
            return cls._recognize_rapidocr(pixmap)
        if backend == "Tesseract":
            return cls._recognize_tesseract(pixmap, language)
        raise OCRUnavailableError("No supported offline OCR backend is available.")

    @classmethod
    def _normalize_page_result(cls, value: OCRPageRecognition | OCRLayoutResult | str) -> OCRPageRecognition:
        # Compatibility with tests and third-party adapters that still return text.
        if isinstance(value, OCRPageRecognition):
            return value
        if isinstance(value, OCRLayoutResult):
            return OCRPageRecognition.from_layout(value)
        text = str(value or "").strip()
        return OCRPageRecognition(
            text=text,
            mode="unstructured-fallback",
            confidence=0.45 if text else 0.0,
            warnings=("OCR adapter returned text without coordinates.",) if text else (),
        )

    @classmethod
    def extract_pdf(
        cls,
        path: str | Path,
        *,
        embedded_pages: list[str] | None = None,
        language: str = "eng",
        dpi: int = DEFAULT_DPI,
        progress_callback: ProgressCallback | None = None,
        cancel_callback: CancelCallback | None = None,
        log_callback: LogCallback | None = None,
        force: bool = False,
    ) -> OCRTextResult:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.suffix.lower() != ".pdf":
            raise OCRProcessingError("OCR currently supports PDF files only.")

        if not force:
            cached = cls.cached_text(source)
            if cached is not None:
                if log_callback:
                    log_callback("Using cached layout-aware offline OCR text.")
                return cached

        availability = cls.availability()
        if not availability.available:
            raise OCRUnavailableError(availability.detail)

        folder = cls.cache_folder(source)
        folder.mkdir(parents=True, exist_ok=True)
        page_folder = folder / "pages"
        page_folder.mkdir(parents=True, exist_ok=True)

        current_manifest = None if force else cls._read_manifest(folder)
        allow_page_cache = current_manifest is not None

        pages_text: list[str] = []
        page_layouts: list[dict[str, Any]] = []
        ocr_pages = 0
        embedded_count = 0
        structured_pages = 0
        timeline_pages = 0
        multi_column_pages = 0
        low_confidence_pages = 0
        matrix = fitz.Matrix(max(1, int(dpi)) / 72.0, max(1, int(dpi)) / 72.0)

        with fitz.open(source) as document:
            total = document.page_count
            correction_profile = find_correction_profile(source, page_count=total)
            supplied = embedded_pages or []
            for index, page in enumerate(document):
                if cancel_callback and cancel_callback():
                    raise OCRProcessingError("OCR was cancelled safely.")

                page_number = index + 1
                existing = supplied[index].strip() if index < len(supplied) else ""
                page_cache = page_folder / f"page_{page_number:05d}.txt"
                layout_cache = page_folder / f"page_{page_number:05d}.layout.json"
                recognition: OCRPageRecognition | None = None

                verified_text = (
                    correction_profile.page_text(page_number)
                    if correction_profile is not None
                    else None
                )
                if verified_text:
                    page_text = verified_text
                    ocr_pages += 1
                    stage = "verified narration correction"
                    layout_record = {
                        "page": page_number,
                        "mode": "verified-profile",
                        "confidence": 1.0,
                        "warnings": [
                            "OCR text was replaced by a verified correction profile for this exact scanned edition."
                        ],
                        "details": {
                            "correction_profile": correction_profile.profile_id,
                            "profile_source": str(correction_profile.source),
                        },
                        "text": page_text,
                        "reading_order": [],
                        "regions": [],
                    }
                    page_cache.write_text(page_text, encoding="utf-8", newline="\n")
                    layout_cache.write_text(
                        json.dumps(layout_record, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
                elif len(existing) >= cls.MIN_EMBEDDED_CHARACTERS:
                    page_text = existing
                    embedded_count += 1
                    stage = "embedded text"
                    layout_record = {
                        "page": page_number,
                        "mode": "embedded",
                        "confidence": 1.0,
                        "warnings": [],
                    }
                elif allow_page_cache and page_cache.is_file() and layout_cache.is_file():
                    try:
                        page_text = page_cache.read_text(encoding="utf-8-sig").strip()
                        layout_record = json.loads(layout_cache.read_text(encoding="utf-8-sig"))
                    except (OSError, ValueError, json.JSONDecodeError):
                        page_text = ""
                        layout_record = {}
                    if page_text:
                        ocr_pages += 1
                        stage = "cached layout-aware OCR"
                    else:
                        recognition = None
                        stage = "offline OCR"
                else:
                    page_text = ""
                    layout_record = {}
                    stage = "offline OCR"

                if len(existing) < cls.MIN_EMBEDDED_CHARACTERS and not page_text:
                    pixmap = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB, alpha=False)
                    recognition = cls._normalize_page_result(
                        cls._recognize_page(pixmap, availability.backend, language)
                    )
                    page_text = recognition.text.strip()
                    layout_record = recognition.to_dict()
                    layout_record["page"] = page_number
                    page_cache.write_text(page_text, encoding="utf-8", newline="\n")
                    layout_cache.write_text(
                        json.dumps(layout_record, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                        newline="\n",
                    )
                    ocr_pages += 1

                mode = str(layout_record.get("mode") or "standard")
                confidence = float(layout_record.get("confidence") or 0.0)
                if mode not in {"embedded", "standard"}:
                    structured_pages += 1
                if mode == "timeline":
                    timeline_pages += 1
                if mode == "multi-column":
                    multi_column_pages += 1
                if mode != "embedded" and confidence < cls.LOW_LAYOUT_CONFIDENCE:
                    low_confidence_pages += 1

                pages_text.append(page_text.strip())
                page_layouts.append(layout_record)
                if progress_callback:
                    progress_callback(page_number, total, stage)
                if log_callback:
                    suffix = ""
                    if mode not in {"embedded", "standard"}:
                        suffix = f" • {mode} reading order"
                    log_callback(f"Page {page_number}/{total}: {stage}{suffix}")

        text = "\n\f\n".join(pages_text).strip()
        if len(text.split()) < cls.MIN_RESULT_WORDS:
            raise OCRProcessingError(
                "Offline OCR finished but did not find enough readable words. "
                "The scan may be too faint, decorative, rotated, or low resolution."
            )

        text_file = folder / "ocr_text.txt"
        manifest_file = folder / "manifest.json"
        layout_report_file = folder / "layout_report.json"
        temporary_text = text_file.with_suffix(".txt.tmp")
        temporary_manifest = manifest_file.with_suffix(".json.tmp")
        temporary_layout = layout_report_file.with_suffix(".json.tmp")
        temporary_text.write_text(text, encoding="utf-8", newline="\n")
        manifest = {
            "schema": cls.CACHE_SCHEMA,
            "layout_schema": cls.LAYOUT_SCHEMA,
            "source": str(source),
            "backend": availability.backend,
            "pages": len(pages_text),
            "ocr_pages": ocr_pages,
            "embedded_pages": embedded_count,
            "structured_pages": structured_pages,
            "timeline_pages": timeline_pages,
            "multi_column_pages": multi_column_pages,
            "low_confidence_pages": low_confidence_pages,
            "correction_profile": correction_profile.profile_id if correction_profile else "",
            "dpi": int(dpi),
        }
        temporary_manifest.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary_layout.write_text(
            json.dumps(
                {
                    "schema": cls.LAYOUT_SCHEMA,
                    "source": str(source),
                    "summary": manifest,
                    "pages": page_layouts,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary_text, text_file)
        os.replace(temporary_manifest, manifest_file)
        os.replace(temporary_layout, layout_report_file)

        return OCRTextResult(
            text=text,
            backend=availability.backend,
            pages=len(pages_text),
            ocr_pages=ocr_pages,
            embedded_pages=embedded_count,
            cache_hit=False,
            cache_folder=folder,
            structured_pages=structured_pages,
            timeline_pages=timeline_pages,
            multi_column_pages=multi_column_pages,
            low_confidence_pages=low_confidence_pages,
            layout_schema=cls.LAYOUT_SCHEMA,
            correction_profile=correction_profile.profile_id if correction_profile else "",
        )
