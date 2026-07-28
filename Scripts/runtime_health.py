from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass
class HealthResult:
    component: str
    ok: bool
    version: str = ""
    detail: str = ""
    python: str = sys.executable
    architecture: str = platform.architecture()[0]


def _version(module: object) -> str:
    return str(getattr(module, "__version__", "unknown"))


def check_torch() -> HealthResult:
    import torch

    tensor = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
    total = float(tensor.sum().item())
    if abs(total - 6.0) > 0.001:
        raise RuntimeError(f"Unexpected tensor result: {total}")
    return HealthResult(
        "torch",
        True,
        _version(torch),
        f"CPU tensor operation passed; CUDA available={torch.cuda.is_available()}",
    )


def check_onnxruntime() -> HealthResult:
    import onnxruntime as ort

    providers = ort.get_available_providers()
    if not providers:
        raise RuntimeError("ONNX Runtime reported no execution providers.")
    return HealthResult(
        "onnxruntime",
        True,
        _version(ort),
        "Providers: " + ", ".join(providers),
    )


def check_rapidocr(initialize: bool = False) -> HealthResult:
    import rapidocr

    detail = "RapidOCR import passed."
    if initialize:
        from rapidocr import RapidOCR

        engine = RapidOCR()
        if engine is None:
            raise RuntimeError("RapidOCR returned no engine instance.")
        detail = "RapidOCR engine initialization passed."
    return HealthResult("rapidocr", True, _version(rapidocr), detail)


def check_kokoro() -> HealthResult:
    import kokoro
    from kokoro import KPipeline

    if KPipeline is None:
        raise RuntimeError("KPipeline is unavailable.")
    return HealthResult(
        "kokoro",
        True,
        _version(kokoro),
        "Kokoro and KPipeline imports passed.",
    )


def check_pyside6() -> HealthResult:
    import PySide6
    from PySide6.QtCore import qVersion

    version = _version(PySide6)
    if version != "6.8.3":
        raise RuntimeError(
            f"Audiobook Studio requires the tested Qt/PySide 6.8.3 runtime; found {version}."
        )
    return HealthResult("PySide6", True, version, f"Qt {qVersion()} LTS")


def check_psutil() -> HealthResult:
    import psutil

    memory = psutil.virtual_memory()
    cpu_count = psutil.cpu_count(logical=True)
    if memory.total <= 0:
        raise RuntimeError("psutil reported no physical memory.")
    if not cpu_count or cpu_count <= 0:
        raise RuntimeError("psutil reported no logical processors.")
    return HealthResult(
        "psutil",
        True,
        _version(psutil),
        f"System metrics passed; logical CPUs={cpu_count}; RAM bytes={memory.total}",
    )


CHECKS: dict[str, Callable[[], HealthResult]] = {
    "torch": check_torch,
    "onnxruntime": check_onnxruntime,
    "rapidocr": check_rapidocr,
    "kokoro": check_kokoro,
    "pyside6": check_pyside6,
    "psutil": check_psutil,
}


def run(component: str, initialize_ocr: bool) -> HealthResult:
    try:
        if component == "rapidocr":
            return check_rapidocr(initialize=initialize_ocr)
        return CHECKS[component]()
    except BaseException as error:  # native import errors are often OSError
        return HealthResult(
            component=component,
            ok=False,
            detail=f"{type(error).__name__}: {error}\n{traceback.format_exc()}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audiobook Studio native runtime health check")
    parser.add_argument("--component", choices=sorted(CHECKS), required=True)
    parser.add_argument("--initialize-ocr", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-json", type=Path)
    args = parser.parse_args()

    # Prevent packages from leaking out of the project-local virtual environment.
    os.environ.setdefault("PYTHONNOUSERSITE", "1")
    result = run(args.component, args.initialize_ocr)
    payload = asdict(result)

    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"{result.component}: {status}")
        if result.version:
            print(f"Version: {result.version}")
        if result.detail:
            print(result.detail.rstrip())
        print(f"Python: {result.python}")
        print(f"Architecture: {result.architecture}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
