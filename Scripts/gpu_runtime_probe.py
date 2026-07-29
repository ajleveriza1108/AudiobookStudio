from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any


REQUIRED_MODULES = (
    "kokoro",
    "numpy",
    "soundfile",
    "PySide6",
    "rapidocr",
    "onnxruntime",
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def probe(project_root: Path, required_name: str = "") -> tuple[bool, dict[str, Any]]:
    started = time.time()
    result: dict[str, Any] = {
        "schema": 1,
        "checked_at_epoch": started,
        "project_root": str(project_root),
        "python": platform.python_version(),
        "executable": sys.executable,
        "requested_mode": "automatic",
        "runtime_mode": "hybrid_cpu_gpu",
        "narration_backend": "unavailable",
        "standard_ocr_backend": "CPU",
        "advanced_ocr_backend": "separate optional runtime",
        "audio_assembly_backend": "CPU",
        "success": False,
        "errors": [],
    }

    missing: list[str] = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as error:
            missing.append(f"{module_name}: {error}")
    if missing:
        result["errors"].extend(missing)
        return False, result

    try:
        import torch

        result["torch_version"] = str(torch.__version__)
        result["torch_cuda_build"] = str(torch.version.cuda or "")
        result["cuda_available"] = bool(torch.cuda.is_available())

        if not torch.cuda.is_available():
            result["errors"].append(
                "CUDA is unavailable inside the dedicated GPU runtime."
            )
            return False, result

        device_index = 0
        name = str(torch.cuda.get_device_name(device_index))
        properties = torch.cuda.get_device_properties(device_index)
        total_vram = int(properties.total_memory)
        capability = tuple(int(value) for value in torch.cuda.get_device_capability(device_index))

        result.update(
            {
                "gpu_index": device_index,
                "gpu_name": name,
                "gpu_vram_bytes": total_vram,
                "gpu_vram_gb": round(total_vram / (1024**3), 2),
                "compute_capability": f"{capability[0]}.{capability[1]}",
            }
        )

        if required_name and required_name.casefold() not in name.casefold():
            result["errors"].append(
                f"Expected a GPU name containing '{required_name}', detected '{name}'."
            )
            return False, result

        # Real CUDA execution test, not detection only.
        left = torch.arange(0, 262144, dtype=torch.float32, device="cuda").reshape(512, 512)
        right = torch.eye(512, dtype=torch.float32, device="cuda")
        output = left @ right
        torch.cuda.synchronize()
        checksum = float(output[0, 0].item() + output[-1, -1].item())
        del left, right, output
        torch.cuda.empty_cache()

        result["cuda_tensor_test"] = "passed"
        result["cuda_tensor_checksum"] = checksum
        result["narration_backend"] = "NVIDIA CUDA"
        result["success"] = True

        try:
            import onnxruntime as ort

            providers = list(ort.get_available_providers())
        except Exception:
            providers = []
        result["onnxruntime_providers"] = providers
        result["standard_ocr_backend"] = (
            "NVIDIA CUDA"
            if "CUDAExecutionProvider" in providers
            else "CPU (stable RapidOCR)"
        )

        return True, result
    except Exception as error:
        result["errors"].append(f"CUDA execution test failed: {error}")
        return False, result
    finally:
        result["elapsed_seconds"] = round(time.time() - started, 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--require-name", default="")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-marker", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    ok, report = probe(project_root, required_name=str(args.require_name or ""))

    report_path = project_root / "Logs" / "gpu_runtime_status.json"
    _write_json(report_path, report)

    marker_path = project_root / ".gpu-runtime-ready.json"
    if ok and not args.no_marker:
        _write_json(marker_path, report)
    elif marker_path.exists():
        marker_path.unlink(missing_ok=True)

    if not args.quiet:
        print("=" * 60)
        print("Audiobook Studio GPU Runtime Check")
        print("=" * 60)
        print(f"Success: {ok}")
        print(f"GPU: {report.get('gpu_name', 'Unavailable')}")
        print(f"VRAM: {report.get('gpu_vram_gb', 'Unknown')} GB")
        print(f"PyTorch: {report.get('torch_version', 'Unavailable')}")
        print(f"CUDA build: {report.get('torch_cuda_build', 'Unavailable')}")
        print(f"Narration: {report.get('narration_backend')}")
        print(f"Standard OCR: {report.get('standard_ocr_backend')}")
        print(f"Audio assembly: {report.get('audio_assembly_backend')}")
        if report.get("errors"):
            print("Errors:")
            for error in report["errors"]:
                print(f"  - {error}")
        print(f"Report: {report_path}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
