from __future__ import annotations

import argparse
import compileall
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from core.paths import PATHS


REQUIRED_FILES = (
    "app.py",
    "requirements.txt",
    "core/project.py",
    "core/generator.py",
    "core/resume.py",
    "core/merger.py",
    "core/book_preparation.py",
    "core/narration_plan.py",
    "core/ocr.py",
    "core/ocr_layout.py",
    "core/audio_quality.py",
    "ui/main_window.py",
    "ui/worker_callbacks.py",
    "ui/thread_manager.py",
    "Scripts/gui_thread_dispatch_probe.py",
    "ui/preview.py",
    "ui/chapter_editor.py",
    "ui/pronunciation_manager.py",
    "workers/generator_worker.py",
    "repair_runtime.ps1",
    "Scripts/runtime_health.py",
)

REQUIRED_IMPORTS = (
    "PySide6",
    "numpy",
    "soundfile",
    "fitz",
    "ebooklib",
    "bs4",
    "mutagen",
    "librosa",
    "psutil",
    "requests",
    "rapidocr",
)

CORE_IMPORTS = (
    "core.audio_quality",
    "core.book_preparation",
    "core.chapters",
    "core.chunker",
    "core.chunk_validator",
    "core.generator",
    "core.merger",
    "core.narration_plan",
    "core.ocr",
    "core.ocr_layout",
    "core.parser",
    "core.pronunciation",
    "core.project",
    "core.resume",
)


def compile_source(root: Path) -> bool:
    excluded = {
        ".git",
        ".venv",
        "Books",
        "Cache",
        "Logs",
        "Models",
        "Output",
        "Projects",
        "Temp",
    }
    pattern = re.compile(r"[\\/](?:" + "|".join(map(re.escape, excluded)) + r")[\\/]")
    return compileall.compile_dir(root, quiet=1, rx=pattern)


def quick_check(root: Path) -> int:
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        print("Missing required files:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 1
    print("Required files: PASS")

    if not compile_source(root):
        print("Python compilation: FAIL", file=sys.stderr)
        return 1
    print("Python compilation: PASS")
    return 0


def full_check(root: Path) -> int:
    if quick_check(root):
        return 1

    if sys.version_info[:2] != (3, 12):
        print(
            f"WARNING: Python {sys.version_info.major}.{sys.version_info.minor} is active. "
            "The supported runtime is Python 3.12."
        )
    else:
        print("Python 3.12: PASS")

    missing_imports: list[str] = []
    for module_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            missing_imports.append(f"{module_name}: {error}")
    if missing_imports:
        print("Required pure-Python packages are unavailable:", file=sys.stderr)
        for item in missing_imports:
            print(f"  - {item}", file=sys.stderr)
        print("Run: .\\repair_runtime.ps1 -ForceRebuild", file=sys.stderr)
        return 1
    print("Required Python packages: PASS")

    # Native libraries are deliberately tested in separate Python processes.
    # A failed Windows DLL import can leave the current process in a poisoned
    # state and make unrelated packages appear broken.
    health_script = root / "Scripts" / "runtime_health.py"
    native_checks = (
        ("torch", False),
        ("onnxruntime", False),
        ("rapidocr", True),
        ("kokoro", False),
        ("pyside6", False),
        ("psutil", False),
    )
    native_failures: list[str] = []
    for component, initialize_ocr in native_checks:
        command = [
            sys.executable,
            "-u",
            str(health_script),
            "--component",
            component,
        ]
        if initialize_ocr:
            command.append("--initialize-ocr")
        completed = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONNOUSERSITE": "1", "CUDA_VISIBLE_DEVICES": ""},
        )
        output = "\n".join(
            value.strip()
            for value in (completed.stdout, completed.stderr)
            if value and value.strip()
        )
        if completed.returncode == 0:
            first_line = output.splitlines()[0] if output else component
            print(f"Native runtime {first_line}")
        else:
            native_failures.append(f"{component}: {output or 'unknown failure'}")
    if native_failures:
        print("Native runtime checks failed:", file=sys.stderr)
        for item in native_failures:
            print(f"  - {item}", file=sys.stderr)
        print("Run: .\\repair_runtime.ps1 -ForceRebuild", file=sys.stderr)
        return 1
    print("Native Windows runtime: PASS")

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if os.name == "nt":
        windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        if windows_fonts.is_dir():
            os.environ.setdefault("QT_QPA_FONTDIR", str(windows_fonts))
    for module_name in CORE_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            print(f"Core import failed for {module_name}: {error}", file=sys.stderr)
            return 1
    print("Core imports: PASS")

    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow

        application = QApplication.instance() or QApplication([])
        window = MainWindow()
        labels = [window.central.preview.tabs.tabText(index) for index in range(window.central.preview.tabs.count())]
        required_tabs = {"Overview", "Cleaned Text", "Preparation", "Chapters"}
        if not required_tabs.issubset(set(labels)):
            raise RuntimeError(f"Missing studio tabs: {sorted(required_tabs.difference(labels))}")
        if window.minimumWidth() > 1100 or window.minimumHeight() > 700:
            raise RuntimeError("The minimum window size is larger than the supported responsive baseline.")

        # Exercise the exact import and first-page preview path that failed in
        # R1.3. This must run before verification can claim the GUI is ready.
        import tempfile
        import fitz

        with tempfile.TemporaryDirectory(prefix="audiobookstudio_verify_") as temporary:
            temporary_path = Path(temporary)
            sample = temporary_path / "verification_book.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "Chapter One\nAudiobook Studio import verification text.")
            document.save(sample)
            document.close()
            window.central.preview.load_book(sample)
            if "import verification" not in window.central.preview.cleaned_text.lower():
                raise RuntimeError("Book import smoke test did not produce cleaned text.")

            # Build a real image-only PDF. The first preview must recognize that
            # OCR is required rather than producing an empty chapter table.
            scanned = temporary_path / "scanned_verification_book.pdf"
            source_document = fitz.open()
            source_page = source_document.new_page(width=900, height=1200)
            source_page.insert_textbox(
                fitz.Rect(80, 180, 820, 700),
                "SCANNED BOOK OCR TEST 1234\nThis page contains image pixels, not embedded PDF text.",
                fontsize=38,
                fontname="helv",
                align=fitz.TEXT_ALIGN_CENTER,
            )
            pixmap = source_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image_bytes = pixmap.tobytes("png")
            source_document.close()

            scanned_document = fitz.open()
            scanned_page = scanned_document.new_page(width=900, height=1200)
            scanned_page.insert_image(scanned_page.rect, stream=image_bytes)
            scanned_document.save(scanned)
            scanned_document.close()

            window.central.preview.load_book(scanned)
            if not window.central.preview.is_ocr_required():
                raise RuntimeError("Image-only PDF was not marked as requiring offline OCR.")
            if window.central.preview.included_chapter_count() != 1:
                raise RuntimeError("Image-only PDF did not receive the Full Book fallback section.")

            from core.chapters import detect_chapters
            from core.ocr import OCRService
            from core.parser import extract_book_text

            ocr_diagnostics = {}
            recognized = extract_book_text(
                scanned,
                ocr_if_needed=True,
                diagnostics=ocr_diagnostics,
            )
            normalized = recognized.upper()
            if not all(word in normalized for word in ("SCANNED", "BOOK", "OCR")):
                raise RuntimeError("Offline OCR smoke test did not recognize the verification text.")
            if not ocr_diagnostics.get("ocr_used"):
                raise RuntimeError("Offline OCR smoke test did not report OCR usage.")
            chapters = detect_chapters(recognized)
            if not chapters:
                raise RuntimeError("OCR text did not receive a narratable section.")
            cached = OCRService.cached_text(scanned)
            if cached is None:
                raise RuntimeError("Offline OCR text was not cached for future launches.")

            # A second preview must load cached OCR text immediately.
            window.central.preview.load_book(scanned)
            if window.central.preview.is_ocr_required():
                raise RuntimeError("Cached OCR text was not reused by the preview.")
            if not window.central.preview.cleaned_text.strip():
                raise RuntimeError("Cached OCR preview did not contain narration text.")

            # Verify the exact R1.14 defect: independent timeline cells must
            # never be flattened across the page as one horizontal sentence.
            timeline_pdf = temporary_path / "timeline_verification_book.pdf"
            timeline_source = fitz.open()
            timeline_page = timeline_source.new_page(width=1200, height=900)
            cells = [
                ("January", "ALPHA EVENT", 120, 110),
                ("February", "BETA EVENT", 500, 110),
                ("March", "GAMMA EVENT", 880, 110),
                ("April", "DELTA EVENT", 120, 470),
                ("May", "EPSILON EVENT", 500, 470),
                ("June", "ZETA EVENT", 880, 470),
            ]
            for month, event, x, y in cells:
                timeline_page.insert_text((x, y), month, fontsize=34, fontname="helv")
                timeline_page.insert_text((x, y + 130), event, fontsize=28, fontname="helv")
            timeline_pixmap = timeline_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            timeline_image = timeline_pixmap.tobytes("png")
            timeline_source.close()
            timeline_document = fitz.open()
            timeline_target = timeline_document.new_page(width=1200, height=900)
            timeline_target.insert_image(timeline_target.rect, stream=timeline_image)
            timeline_document.save(timeline_pdf)
            timeline_document.close()

            timeline_diagnostics = {}
            timeline_text = extract_book_text(
                timeline_pdf, ocr_if_needed=True, diagnostics=timeline_diagnostics
            )
            if int(timeline_diagnostics.get("timeline_pages") or 0) < 1:
                raise RuntimeError("Layout-aware OCR did not detect the verification timeline.")
            timeline_lower = timeline_text.casefold()
            month_positions = [timeline_lower.find(name) for name in ("january:", "february:", "march:")]
            if any(position < 0 for position in month_positions) or month_positions != sorted(month_positions):
                raise RuntimeError("Timeline cells were not ordered month by month.")
            if "alpha event beta event gamma event" in timeline_lower:
                raise RuntimeError("Timeline descriptions were flattened across unrelated columns.")

            import shutil
            shutil.rmtree(OCRService.cache_folder(scanned), ignore_errors=True)
            shutil.rmtree(OCRService.cache_folder(timeline_pdf), ignore_errors=True)

        window.close()
        application.processEvents()
        print("Responsive GUI, scanned PDF, structured timeline OCR, and offline OCR smoke tests: PASS")

        if os.name == "nt":
            dispatch_env = {**os.environ, "PYTHONNOUSERSITE": "1", "CUDA_VISIBLE_DEVICES": ""}
            dispatch_env.pop("QT_QPA_PLATFORM", None)
            dispatch_probe = subprocess.run(
                [
                    sys.executable,
                    "-u",
                    str(root / "Scripts" / "gui_thread_dispatch_probe.py"),
                    "--visible",
                    "--updates",
                    "4000",
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=40,
                env=dispatch_env,
            )
            dispatch_output = "\n".join(
                value.strip()
                for value in (dispatch_probe.stdout, dispatch_probe.stderr)
                if value and value.strip()
            )
            if dispatch_probe.returncode != 0:
                raise RuntimeError(
                    "The worker-to-GUI thread dispatch probe failed "
                    f"(exit code {dispatch_probe.returncode}).\n{dispatch_output}"
                )
            print(dispatch_output or "GUI worker-to-main-thread dispatch probe: PASS")

            real_gui = subprocess.run(
                [sys.executable, "-u", str(root / "Scripts" / "gui_startup_probe.py"), "--visible-ms", "8000"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=50,
                env={**os.environ, "PYTHONNOUSERSITE": "1", "CUDA_VISIBLE_DEVICES": ""},
            )
            output = "\n".join(
                value.strip()
                for value in (real_gui.stdout, real_gui.stderr)
                if value and value.strip()
            )
            if real_gui.returncode != 0:
                raise RuntimeError(
                    "The real Windows renderer failed its startup probe "
                    f"(exit code {real_gui.returncode}).\n{output}"
                )
            print(output or "Real Windows GUI startup probe: PASS")
    except Exception as error:
        print(f"Responsive GUI smoke test failed: {error}", file=sys.stderr)
        return 1

    # Run pytest through a small exit guard.  On Windows, PySide can corrupt
    # its heap during interpreter teardown after pytest has already returned
    # success.  Native failures during a test still terminate before the guard.
    tests = subprocess.run(
        [sys.executable, "-u", str(root / "Scripts" / "pytest_exit_guard.py"), "-q"],
        cwd=root,
        check=False,
        text=True,
        env={**os.environ, "PYTHONNOUSERSITE": "1", "CUDA_VISIBLE_DEVICES": ""},
    )
    if tests.returncode != 0:
        print("Automated regression tests: FAIL", file=sys.stderr)
        return tests.returncode
    print("Automated regression tests: PASS")

    from core.ffmpeg import FFmpeg
    from engines.manager import EngineManager

    manager = EngineManager()
    if manager.errors:
        print("Engine manifest errors:", file=sys.stderr)
        print(json.dumps(manager.errors, indent=2), file=sys.stderr)
        return 1
    engine_records = manager.available()
    kokoro = next((item for item in engine_records if item.get("name") == "kokoro"), None)
    if not kokoro or kokoro.get("status") != "Available":
        missing = ", ".join((kokoro or {}).get("missing_dependencies", []) or [])
        print(
            "Kokoro production engine: FAIL"
            + (f" (missing: {missing})" if missing else ""),
            file=sys.stderr,
        )
        print(r"Run: .\install_dependencies.ps1", file=sys.stderr)
        return 1
    print("Kokoro production engine: PASS")
    print("TTS engine manifests:")
    print(json.dumps(engine_records, indent=2))

    executable = FFmpeg.executable()
    if executable:
        print(f"FFmpeg: FOUND ({executable})")
    else:
        print("FFmpeg: NOT FOUND (WAV works; MP3 and M4B require FFmpeg)")

    PATHS.ensure_runtime_directories()
    print("Runtime folders: PASS")
    print("Audiobook Studio v0.3.0 R1.16 verification passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run file and syntax checks only.")
    arguments = parser.parse_args()
    root = PATHS.project_root
    print(f"Project root: {root}", flush=True)
    return quick_check(root) if arguments.quick else full_check(root)


if __name__ == "__main__":
    raise SystemExit(main())
