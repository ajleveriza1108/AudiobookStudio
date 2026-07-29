from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_verification_script_uses_numeric_last_exit_code():
    script = (ROOT / "run_phase3_checks.ps1").read_text(encoding="utf-8-sig")

    assert "$Code = Invoke-PythonCommand" not in script
    assert "$code = $LASTEXITCODE" in script
    assert "& $VenvPython @arguments" in script
    assert ".venv\\Scripts\\python.exe" in script


def test_launcher_uses_numeric_last_exit_code():
    script = (ROOT / "launch_audiobook_studio.ps1").read_text(encoding="utf-8-sig")

    assert "$Code = Invoke-StudioPython" not in script
    assert "$code = $LASTEXITCODE" in script
    assert ("& $RuntimePython -u \"app.py\"" in script or "& $VenvPython -u \"app.py\"" in script)
    assert ".venv\\Scripts\\python.exe" in script
    assert ".gpu-venv\\Scripts\\python.exe" in script


def test_no_function_assigns_console_output_to_exit_code():
    for relative in ("run_phase3_checks.ps1", "launch_audiobook_studio.ps1"):
        text = (ROOT / relative).read_text(encoding="utf-8-sig")
        assert "$Code = Invoke-" not in text, relative
        assert "$code = Invoke-" not in text, relative
