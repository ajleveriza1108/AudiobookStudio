from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def test_runtime_is_project_local_only():
    verifier = read("run_phase3_checks.ps1")
    launcher = read("launch_audiobook_studio.ps1")
    assert '.venv\\Scripts\\python.exe' in verifier
    assert '.venv\\Scripts\\python.exe' in launcher
    assert "py -3.12 (system installation)" not in verifier
    assert "py -3.12 (system installation)" not in launcher
    assert "PYTHONNOUSERSITE" in verifier
    assert "PYTHONNOUSERSITE" in launcher


def test_repair_installs_official_cpu_torch_and_vc_runtime():
    repair = read("repair_runtime.ps1")
    assert 'https://aka.ms/vs/17/release/vc_redist.x64.exe' in repair
    assert 'https://download.pytorch.org/whl/cpu' in repair
    assert '$TorchVersion = "2.6.0"' in repair
    assert 'Start-Process' in repair
    assert '-Verb RunAs' in repair


def test_native_components_are_checked_separately():
    verifier = read("verify_phase3.py")
    health = read("Scripts/runtime_health.py")
    assert "runtime_health.py" in verifier
    assert "subprocess.run" in verifier
    assert "check_torch" in health
    assert "check_onnxruntime" in health
    assert "CPU tensor operation passed" in health
    assert "RapidOCR engine initialization passed" in health


def test_native_versions_are_pinned():
    requirements = read("requirements.txt")
    assert "onnxruntime==1.22.1" in requirements
    assert "rapidocr==3.9.2" in requirements
    assert "kokoro==0.9.4" in requirements
    assert "misaki[en]==0.9.4" in requirements
    assert "psutil>=6.1,<8" in requirements
    assert "\ntorch" not in requirements.lower()
