from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import struct
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import psutil

from core.config import Config
from core.optional_engines import advanced_ocr_runtime_ready
from core.paths import PATHS


REPORT_SCHEMA = 1
REPORT_FILE = PATHS.logs / "advanced_ocr_capability.json"


@dataclass(frozen=True)
class GPUProbe:
    name: str = ""
    memory_gb: float = 0.0
    driver_version: str = ""
    cuda_version: str = ""
    compute_capability: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "memory_gb": round(self.memory_gb, 2),
            "driver_version": self.driver_version,
            "cuda_version": self.cuda_version,
            "compute_capability": self.compute_capability,
        }


class AdvancedOCRCompatibility:
    """Conservative local capability check for the optional Unlimited-OCR module.

    The check does not import CUDA PyTorch and does not download anything. It
    records only a compact hardware summary needed to decide whether the
    optional module should be offered on this installation.
    """

    SUPPORTED_VRAM_GB = 12.0
    EXPERIMENTAL_VRAM_GB = 8.0
    SUPPORTED_RAM_GB = 24.0
    EXPERIMENTAL_RAM_GB = 16.0
    SUPPORTED_DISK_GB = 30.0
    EXPERIMENTAL_DISK_GB = 20.0
    SUPPORTED_CORES = 8
    EXPERIMENTAL_CORES = 4
    SUPPORTED_COMPUTE = 8.0
    EXPERIMENTAL_COMPUTE = 7.5

    @staticmethod
    def _run(command: list[str], timeout: int = 8) -> subprocess.CompletedProcess[str]:
        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )

    @staticmethod
    def _find_nvidia_smi() -> str:
        found = shutil.which("nvidia-smi")
        if found:
            return found
        candidates: list[Path] = []
        windows = os.getenv("WINDIR", "").strip()
        program_files = os.getenv("ProgramW6432", os.getenv("ProgramFiles", "")).strip()
        if windows:
            candidates.append(Path(windows) / "System32" / "nvidia-smi.exe")
        if program_files:
            candidates.append(
                Path(program_files) / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe"
            )
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return ""

    @classmethod
    def _probe_nvidia(
        cls,
        runner: Callable[[list[str], int], subprocess.CompletedProcess[str]] | None = None,
    ) -> GPUProbe:
        executable = cls._find_nvidia_smi()
        if not executable:
            return GPUProbe()
        run = runner or cls._run

        cuda_version = ""
        try:
            banner = run([executable], 8)
            match = re.search(r"CUDA Version:\s*([0-9.]+)", banner.stdout or "")
            if match:
                cuda_version = match.group(1)
        except (OSError, subprocess.SubprocessError):
            pass

        queries = [
            ["name", "memory.total", "driver_version", "compute_cap"],
            ["name", "memory.total", "driver_version"],
        ]
        rows: list[GPUProbe] = []
        for fields in queries:
            command = [
                executable,
                f"--query-gpu={','.join(fields)}",
                "--format=csv,noheader,nounits",
            ]
            try:
                completed = run(command, 8)
            except (OSError, subprocess.SubprocessError):
                continue
            if completed.returncode != 0 or not completed.stdout.strip():
                continue
            for line in completed.stdout.splitlines():
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 3:
                    continue
                try:
                    memory_gb = float(parts[1]) / 1024.0
                except ValueError:
                    memory_gb = 0.0
                compute: float | None = None
                if len(parts) >= 4:
                    try:
                        compute = float(parts[3])
                    except ValueError:
                        compute = None
                rows.append(
                    GPUProbe(
                        name=parts[0],
                        memory_gb=memory_gb,
                        driver_version=parts[2],
                        cuda_version=cuda_version,
                        compute_capability=compute,
                    )
                )
            if rows:
                break
        return max(rows, key=lambda item: item.memory_gb, default=GPUProbe())

    @staticmethod
    def _installation_key(project_root: Path, gpu_name: str) -> str:
        material = f"{project_root.resolve()}|{platform.node()}|{gpu_name}".encode(
            "utf-8", errors="ignore"
        )
        return hashlib.sha256(material).hexdigest()[:16]

    @classmethod
    def check(
        cls,
        *,
        project_root: str | Path | None = None,
        runner: Callable[[list[str], int], subprocess.CompletedProcess[str]] | None = None,
        gpu_override: GPUProbe | None = None,
        system_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        root = Path(project_root or PATHS.project_root).resolve()
        override = dict(system_override or {})
        system_name = str(override.get("system", platform.system()))
        release = str(override.get("release", platform.release()))
        machine = str(override.get("machine", platform.machine()))
        pointer_bits = int(override.get("pointer_bits", struct.calcsize("P") * 8))
        logical_cores = int(
            override.get("logical_cores", psutil.cpu_count(logical=True) or 1)
        )
        ram_gb = float(
            override.get("ram_gb", psutil.virtual_memory().total / (1024**3))
        )
        try:
            disk_gb = float(
                override.get("disk_free_gb", shutil.disk_usage(root).free / (1024**3))
            )
        except OSError:
            disk_gb = float(override.get("disk_free_gb", 0.0))
        gpu = gpu_override or cls._probe_nvidia(runner)

        reasons: list[str] = []
        recommendations: list[str] = []
        try:
            windows_major = int(re.match(r"\d+", release).group(0))
        except (AttributeError, ValueError):
            windows_major = 0
        windows_64 = (
            system_name.casefold() == "windows"
            and pointer_bits == 64
            and windows_major >= 10
        )
        has_nvidia = bool(gpu.name and gpu.memory_gb > 0)

        experimental_requirements = {
            "windows_64_bit": windows_64,
            "nvidia_gpu": has_nvidia,
            "vram_at_least_8_gb": gpu.memory_gb >= cls.EXPERIMENTAL_VRAM_GB,
            "ram_at_least_16_gb": ram_gb >= cls.EXPERIMENTAL_RAM_GB,
            "disk_at_least_20_gb": disk_gb >= cls.EXPERIMENTAL_DISK_GB,
            "logical_cores_at_least_4": logical_cores >= cls.EXPERIMENTAL_CORES,
            "compute_capability": (
                gpu.compute_capability is None
                or gpu.compute_capability >= cls.EXPERIMENTAL_COMPUTE
            ),
        }
        supported_requirements = {
            "windows_64_bit": windows_64,
            "nvidia_gpu": has_nvidia,
            "vram_at_least_12_gb": gpu.memory_gb >= cls.SUPPORTED_VRAM_GB,
            "ram_at_least_24_gb": ram_gb >= cls.SUPPORTED_RAM_GB,
            "disk_at_least_30_gb": disk_gb >= cls.SUPPORTED_DISK_GB,
            "logical_cores_at_least_8": logical_cores >= cls.SUPPORTED_CORES,
            "compute_capability_8_or_newer": (
                gpu.compute_capability is not None
                and gpu.compute_capability >= cls.SUPPORTED_COMPUTE
            ),
        }

        if all(supported_requirements.values()):
            status = "supported"
            can_enable = True
            summary = "This laptop meets the supported Advanced OCR target."
        elif all(experimental_requirements.values()):
            status = "experimental"
            can_enable = True
            summary = (
                "This laptop may run Advanced OCR, but it is below the supported target."
            )
            recommendations.append(
                "Use one page at a time and keep RapidOCR fallback enabled."
            )
        else:
            status = "unsupported"
            can_enable = False
            summary = "This laptop does not meet the minimum Advanced OCR requirements."

        if not windows_64:
            reasons.append("Windows 10/11 64-bit is required.")
        if not has_nvidia:
            reasons.append("A supported NVIDIA GPU was not detected.")
        elif gpu.memory_gb < cls.EXPERIMENTAL_VRAM_GB:
            reasons.append("At least 8 GB NVIDIA VRAM is required for experimental use.")
        elif gpu.memory_gb < cls.SUPPORTED_VRAM_GB:
            recommendations.append("12 GB or more NVIDIA VRAM is the supported target.")
        if gpu.compute_capability is not None:
            if gpu.compute_capability < cls.EXPERIMENTAL_COMPUTE:
                reasons.append("The NVIDIA GPU architecture is too old for this BF16 model.")
            elif gpu.compute_capability < cls.SUPPORTED_COMPUTE:
                recommendations.append("An Ampere-generation or newer NVIDIA GPU is recommended.")
        else:
            recommendations.append(
                "GPU compute capability could not be confirmed; final runtime verification is required."
            )
        if ram_gb < cls.EXPERIMENTAL_RAM_GB:
            reasons.append("At least 16 GB system RAM is required.")
        elif ram_gb < cls.SUPPORTED_RAM_GB:
            recommendations.append("24–32 GB system RAM is recommended.")
        if disk_gb < cls.EXPERIMENTAL_DISK_GB:
            reasons.append("At least 20 GB free space is required on the app drive.")
        elif disk_gb < cls.SUPPORTED_DISK_GB:
            recommendations.append("30 GB or more free SSD space is recommended.")
        if logical_cores < cls.EXPERIMENTAL_CORES:
            reasons.append("At least four logical CPU cores are required.")
        elif logical_cores < cls.SUPPORTED_CORES:
            recommendations.append("Eight logical CPU cores are recommended.")

        checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        report = {
            "schema": REPORT_SCHEMA,
            "checked_at": checked_at,
            "installation_key": cls._installation_key(root, gpu.name),
            "status": status,
            "can_enable": can_enable,
            "summary": summary,
            "reasons": reasons,
            "recommendations": recommendations,
            "system": {
                "os": system_name,
                "release": release,
                "machine": machine,
                "pointer_bits": pointer_bits,
                "logical_cores": logical_cores,
                "ram_gb": round(ram_gb, 2),
                "disk_free_gb": round(disk_gb, 2),
            },
            "gpu": gpu.to_dict(),
            "runtime": {
                "installed": bool(advanced_ocr_runtime_ready()),
                "model": "baidu/Unlimited-OCR",
                "model_revision": "d549bb9d6a055dbe291408916d66acc2cd5920f6",
            },
            "thresholds": {
                "supported_vram_gb": cls.SUPPORTED_VRAM_GB,
                "experimental_vram_gb": cls.EXPERIMENTAL_VRAM_GB,
                "supported_ram_gb": cls.SUPPORTED_RAM_GB,
                "experimental_ram_gb": cls.EXPERIMENTAL_RAM_GB,
                "supported_disk_gb": cls.SUPPORTED_DISK_GB,
                "experimental_disk_gb": cls.EXPERIMENTAL_DISK_GB,
            },
        }
        return report

    @staticmethod
    def record(
        report: dict[str, Any],
        *,
        report_file: str | Path | None = None,
        config: Config | None = None,
    ) -> Path:
        target = Path(report_file or REPORT_FILE)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, target)
        settings = config or Config()
        settings.update(
            {
                "advanced_ocr_last_checked_at": str(report.get("checked_at") or ""),
                "advanced_ocr_status": str(report.get("status") or "unknown"),
                "advanced_ocr_report": str(target),
                "advanced_ocr_can_enable": bool(report.get("can_enable")),
            }
        )
        return target

    @classmethod
    def check_and_record(
        cls,
        *,
        project_root: str | Path | None = None,
        report_file: str | Path | None = None,
        config: Config | None = None,
    ) -> dict[str, Any]:
        report = cls.check(project_root=project_root)
        cls.record(report, report_file=report_file, config=config)
        return report

    @staticmethod
    def load_report(report_file: str | Path | None = None) -> dict[str, Any] | None:
        target = Path(report_file or REPORT_FILE)
        if not target.is_file():
            return None
        try:
            value = json.loads(target.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(value, dict) or int(value.get("schema") or 0) != REPORT_SCHEMA:
            return None
        return value

    @classmethod
    def enabled_and_ready(cls, config: Config | None = None) -> bool:
        settings = config or Config()
        if not bool(settings.get("advanced_ocr_enabled", False)):
            return False
        report = cls.load_report()
        return bool(
            report
            and report.get("can_enable")
            and advanced_ocr_runtime_ready()
        )

    @staticmethod
    def display_summary(report: dict[str, Any] | None) -> str:
        if not report:
            return "Laptop capability has not been checked yet."
        system = report.get("system") or {}
        gpu = report.get("gpu") or {}
        parts = [str(report.get("summary") or "Capability check completed.")]
        if gpu.get("name"):
            parts.append(
                f"GPU: {gpu.get('name')} ({float(gpu.get('memory_gb') or 0):.1f} GB VRAM)."
            )
        parts.append(
            f"RAM: {float(system.get('ram_gb') or 0):.1f} GB; "
            f"free space: {float(system.get('disk_free_gb') or 0):.1f} GB."
        )
        if report.get("runtime", {}).get("installed"):
            parts.append("Advanced OCR runtime is installed.")
        elif report.get("can_enable"):
            parts.append("The optional Advanced OCR runtime is not installed yet.")
        reasons = list(report.get("reasons") or [])
        if reasons:
            parts.append(" ".join(str(item) for item in reasons))
        return " ".join(parts)
