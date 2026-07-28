from __future__ import annotations

import importlib.util
from pathlib import Path


class FakeGenerate:
    def __init__(self):
        self.enabled = None

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)


def _button_state_class():
    path = Path(__file__).resolve().parents[1] / "ui" / "layouts" / "button_state.py"
    spec = importlib.util.spec_from_file_location("r14_button_state", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ButtonState


def test_generate_requires_book_output_and_engine():
    ButtonState = _button_state_class()
    generate = FakeGenerate()
    state = ButtonState(generate)
    assert generate.enabled is False

    state.set_book(True)
    state.set_output(True)
    assert generate.enabled is False

    state.set_engine(True)
    assert generate.enabled is True

    state.set_engine(False)
    assert generate.enabled is False
