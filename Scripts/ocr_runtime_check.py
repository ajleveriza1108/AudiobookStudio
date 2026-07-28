from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
import traceback
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class OCRCheckResult:
    ready: bool
    initialized: bool
    python: str
    python_version: str
    platform: str
    rapidocr_version: str | None = None
    onnxruntime_version: str | None = None
    error_type: str | None = None
    error_message: str | None = None


def package_version(distribution_name: str) -> str | None:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_check(initialize: bool) -> OCRCheckResult:
    result = OCRCheckResult(
        ready=False,
        initialized=False,
        python=sys.executable,
        python_version=platform.python_version(),
        platform=platform.platform(),
        rapidocr_version=package_version("rapidocr"),
        onnxruntime_version=package_version("onnxruntime"),
    )

    try:
        import onnxruntime  # noqa: F401
        from rapidocr import RapidOCR

        result.rapidocr_version = package_version("rapidocr")
        result.onnxruntime_version = getattr(onnxruntime, "__version__", None) or package_version(
            "onnxruntime"
        )
        if initialize:
            RapidOCR()
            result.initialized = True
        result.ready = True
        return result
    except Exception as error:  # pragma: no cover - exercised on the user's runtime
        result.error_type = type(error).__name__
        result.error_message = str(error)
        traceback.print_exc(file=sys.stderr)
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initialize", action="store_true")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()

    result = run_check(arguments.initialize)
    payload: dict[str, Any] = asdict(result)
    if arguments.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"Python: {result.python}")
        print(f"Version: {result.python_version}")
        print(f"RapidOCR: {result.rapidocr_version or 'not installed'}")
        print(f"ONNX Runtime: {result.onnxruntime_version or 'not installed'}")
        print(f"OCR initialized: {'yes' if result.initialized else 'no'}")
        if result.error_message:
            print(f"Error: {result.error_type}: {result.error_message}")

    if result.ready:
        return 0
    if result.rapidocr_version is None or result.onnxruntime_version is None:
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
