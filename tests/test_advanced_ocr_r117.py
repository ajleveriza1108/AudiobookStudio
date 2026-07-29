from __future__ import annotations

import json
from pathlib import Path

from core.advanced_ocr import AdvancedOCRCompatibility, GPUProbe
from core.config import Config
from core.unlimited_ocr import narration_text_from_markdown, repetition_problem


def supported_system(**overrides):
    values = {
        "system": "Windows",
        "release": "11",
        "machine": "AMD64",
        "pointer_bits": 64,
        "logical_cores": 16,
        "ram_gb": 32.0,
        "disk_free_gb": 80.0,
    }
    values.update(overrides)
    return values


def test_supported_laptop_report():
    report = AdvancedOCRCompatibility.check(
        project_root=Path.cwd(),
        gpu_override=GPUProbe(
            name="NVIDIA GeForce RTX 4070 Ti SUPER",
            memory_gb=16.0,
            driver_version="600.00",
            cuda_version="12.9",
            compute_capability=8.9,
        ),
        system_override=supported_system(),
    )
    assert report["status"] == "supported"
    assert report["can_enable"] is True
    assert report["gpu"]["memory_gb"] == 16.0


def test_experimental_laptop_report():
    report = AdvancedOCRCompatibility.check(
        project_root=Path.cwd(),
        gpu_override=GPUProbe(
            name="NVIDIA GeForce RTX 3070",
            memory_gb=8.0,
            driver_version="600.00",
            cuda_version="12.9",
            compute_capability=8.6,
        ),
        system_override=supported_system(ram_gb=16.0, disk_free_gb=22.0),
    )
    assert report["status"] == "experimental"
    assert report["can_enable"] is True
    assert report["recommendations"]


def test_unsupported_laptop_without_nvidia():
    report = AdvancedOCRCompatibility.check(
        project_root=Path.cwd(),
        gpu_override=GPUProbe(),
        system_override=supported_system(),
    )
    assert report["status"] == "unsupported"
    assert report["can_enable"] is False
    assert any("NVIDIA" in item for item in report["reasons"])


def test_report_is_recorded_atomically(tmp_path):
    defaults = tmp_path / "config.json"
    user = tmp_path / "config.local.json"
    defaults.write_text("{}\n", encoding="utf-8")
    config = Config(defaults_file=defaults, user_file=user)
    report = AdvancedOCRCompatibility.check(
        project_root=tmp_path,
        gpu_override=GPUProbe(
            name="NVIDIA RTX 4090",
            memory_gb=24.0,
            driver_version="600.00",
            cuda_version="12.9",
            compute_capability=8.9,
        ),
        system_override=supported_system(),
    )
    report_file = tmp_path / "capability.json"
    AdvancedOCRCompatibility.record(report, report_file=report_file, config=config)
    saved = json.loads(report_file.read_text(encoding="utf-8"))
    assert saved["status"] == "supported"
    assert config.get("advanced_ocr_can_enable") is True
    assert config.get("advanced_ocr_report") == str(report_file)


def test_markdown_is_cleaned_for_narration():
    source = """# Timeline\n\n| January | First event |\n|---|---|\n- Next item\n"""
    assert narration_text_from_markdown(source) == (
        "Timeline\n\nJanuary. First event\nNext item"
    )


def test_repetition_guard_rejects_loop():
    text = "\n".join(["The same repeated OCR sentence appears here."] * 6)
    assert "repeated" in repetition_problem(text).lower()
