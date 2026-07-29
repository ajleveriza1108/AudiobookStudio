from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_r11772_version_contract():
    source = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    assert 'R1.17.7.5' in source
    assert 'BUILD = 1775' in source


def test_launcher_prefers_gpu_without_removing_cpu_fallback():
    source = (ROOT / "launch_audiobook_studio.ps1").read_text(encoding="utf-8-sig")
    assert '.gpu-venv\\Scripts\\python.exe' in source
    assert 'AUDIOBOOK_STUDIO_DEVICE = "cuda"' in source
    assert 'AUDIOBOOK_STUDIO_DEVICE = "cpu"' in source
    assert 'CUDA_VISIBLE_DEVICES = ""' not in source
    assert '--require-name "RTX 2050"' in source
    assert 'PDF, text preparation, standard OCR, and audio assembly: CPU' in source


def test_gpu_probe_runs_real_cuda_tensor_test():
    source = (ROOT / "Scripts" / "gpu_runtime_probe.py").read_text(encoding="utf-8")
    assert 'torch.cuda.is_available()' in source
    assert 'torch.cuda.synchronize()' in source
    assert 'left @ right' in source
    assert '"runtime_mode": "hybrid_cpu_gpu"' in source
    assert 'result["narration_backend"] = "NVIDIA CUDA"' in source


def test_gpu_installer_isolated_and_pinned():
    source = (ROOT / "install_gpu_runtime.ps1").read_text(encoding="utf-8-sig")
    assert '.gpu-venv' in source
    assert 'torch==2.6.0' in source
    assert 'https://download.pytorch.org/whl/cu124' in source
    assert 'RTX\\s*2050' in source
    assert 'The protected CPU runtime was not modified.' in source


def test_gpu_config_defaults_are_automatic():
    defaults = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert defaults["processing_device"] == "auto"
    assert defaults["gpu_runtime_enabled"] is True


def test_r11772_preserves_gpu_selected_source_and_structured_ocr_features():
    version = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    project = (ROOT / "core" / "project.py").read_text(encoding="utf-8")
    config = (ROOT / "core" / "config.py").read_text(encoding="utf-8")
    assert "R1.17.7.5" in version
    assert "expected_source_sha256" in project
    assert "Selected Source.json" in project
    assert "removed_books" in config
    assert (ROOT / "core" / "ocr_structured.py").is_file()
    assert '"processing_device": "auto"' in config
    assert not (ROOT / "Resources" / "OCRCorrections" / "remember_when_1945.json").exists()


def test_nvidia_smi_detection_is_windows_powershell_51_safe():
    source = (ROOT / "install_gpu_runtime.ps1").read_text(encoding="utf-8-sig")
    assert "function Resolve-NvidiaSmiPath" in source
    assert '$Command.PSObject.Properties[$PropertyName]' in source
    assert '@("Source", "Path", "Definition")' in source
    assert "$NvidiaSmi.FullName" not in source
    assert "Invoke-NativeCapture" in source
    assert 'Write-Host "nvidia-smi: $NvidiaSmiPath"' in source


def test_nvidia_smi_query_is_diagnostic_not_a_hard_gate():
    source = (ROOT / "install_gpu_runtime.ps1").read_text(encoding="utf-8-sig")
    assert "function Get-NvidiaAdapterName" in source
    assert "Get-CimInstance" in source
    assert "Get-WmiObject" in source
    assert "function Invoke-NativeCapture" in source
    assert "nvidia-smi diagnostic query was unavailable and will not block installation" in source
    assert "The post-install PyTorch CUDA tensor test is the authoritative GPU gate" in source
    assert 'throw "nvidia-smi could not query the laptop GPU."' not in source


def test_exact_rtx_2050_is_still_required_before_download():
    source = (ROOT / "install_gpu_runtime.ps1").read_text(encoding="utf-8-sig")
    assert '$DetectedAdapter = $AdapterNames' in source
    assert 'Where-Object { $_ -match "RTX\\s*2050" }' in source
    assert "NVIDIA GeForce RTX 2050 detected by Windows" in source


def test_release_source_contains_no_generated_source_cache():
    forbidden_directories = {".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache"}
    forbidden_suffixes = {".pyc", ".pyo"}
    excluded_roots = {
        ".venv", ".gpu-venv", ".advanced-ocr-venv", ".git",
        "Books", "Cache", "Logs", "Models", "Output", "Projects", "Temp", "Voices",
    }

    offenders = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not relative.parts:
            continue
        if relative.parts[0] in excluded_roots or relative.parts[0].startswith("_backup_"):
            continue
        if any(part in forbidden_directories for part in relative.parts):
            offenders.append(relative.as_posix())
        elif path.is_file() and path.suffix.lower() in forbidden_suffixes:
            offenders.append(relative.as_posix())

    assert offenders == [], f"Generated source cache files must not be packaged: {offenders}"


def test_r11771_update_installer_uses_isolated_verification_when_present():
    installers = list(ROOT.parent.glob("install_v030_r1_17_7_1.ps1"))
    if not installers:
        return
    source = installers[0].read_text(encoding="utf-8-sig")
    assert "installed-verification-source" in source
    assert "PYTHONPYCACHEPREFIX" in source
    assert "-p", "no:cacheprovider"
