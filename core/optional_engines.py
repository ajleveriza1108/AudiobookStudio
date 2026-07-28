from __future__ import annotations

import os
from pathlib import Path

from core.paths import PATHS


def voice_runtime_python() -> Path:
    root = PATHS.project_root / ".voice-venv"
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def chatterbox_runtime_ready() -> bool:
    marker = PATHS.project_root / ".voice-venv" / ".audiobookstudio_chatterbox_ready.json"
    return (
        voice_runtime_python().is_file()
        and (PATHS.project_root / "Scripts" / "chatterbox_worker.py").is_file()
        and marker.is_file()
    )


def chatterbox_runtime_summary() -> str:
    if chatterbox_runtime_ready():
        return "Optional Chatterbox voice-cloning runtime installed"
    return "Optional voice-cloning module not installed"
