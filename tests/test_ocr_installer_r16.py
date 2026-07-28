from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_native_process_helper_is_installed():
    helper = ROOT / "Scripts" / "native_process.ps1"
    text = helper.read_text(encoding="utf-8-sig")
    assert "System.Diagnostics.ProcessStartInfo" in text
    assert "RedirectStandardError" in text
    assert "Invoke-NativeProcess" in text


def test_ocr_installer_uses_project_runtime_or_permanent_repair():
    text = (ROOT / "install_ocr.ps1").read_text(encoding="utf-8-sig")
    assert "2>$null" not in text
    assert '.venv\\Scripts\\python.exe' in text
    assert "runtime_health.py" in text
    assert "repair_runtime.ps1" in text


def test_dependency_and_runtime_scripts_do_not_capture_console_as_exit_code():
    for relative in (
        "install_dependencies.ps1",
        "run_phase3_checks.ps1",
        "launch_audiobook_studio.ps1",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8-sig")
        assert "2>$null" not in text, relative
        assert "$Code = Invoke-PythonCommand" not in text, relative
        assert "$Code = Invoke-StudioPython" not in text, relative


def test_ocr_runtime_checker_reports_structured_status():
    checker = (ROOT / "Scripts" / "ocr_runtime_check.py").read_text(encoding="utf-8")
    assert "OCRCheckResult" in checker
    assert "RapidOCR()" in checker
    assert "--initialize" in checker
    assert "json.dumps" in checker


def test_requirements_pin_tested_rapidocr_release():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "rapidocr==3.9.2" in requirements
