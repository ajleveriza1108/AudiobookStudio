from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def test_direct_runtime_dependencies_are_declared():
    requirements = read("requirements.txt").lower()
    assert "psutil>=6.1,<8" in requirements
    assert "requests>=2.32,<3" in requirements


def test_psutil_is_checked_before_gui_construction():
    verifier = read("verify_phase3.py")
    assert '"psutil"' in verifier
    assert '"requests"' in verifier
    assert '("psutil", False)' in verifier


def test_runtime_health_exercises_real_system_metrics():
    health = read("Scripts/runtime_health.py")
    assert "def check_psutil" in health
    assert "psutil.virtual_memory()" in health
    assert "psutil.cpu_count" in health
    assert '"psutil": check_psutil' in health


def test_launcher_and_repair_cover_psutil():
    launcher = read("launch_audiobook_studio.ps1")
    repair = read("repair_runtime.ps1")
    assert "--component psutil" in launcher
    assert '-Component "psutil"' in repair
    assert '@{ Name = "psutil"; OCR = $false }' in repair


def test_focused_repair_does_not_rebuild_large_runtime():
    patch = read("repair_r18_dependencies.ps1")
    assert 'psutil>=6.1,<8' in patch
    assert 'requests>=2.32,<3' in patch
    assert "torch==" not in patch
    assert "& $repair -ForceRebuild" not in patch
