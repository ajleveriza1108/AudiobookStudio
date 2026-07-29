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

def advanced_ocr_runtime_root() -> Path:
    return PATHS.project_root / ".advanced-ocr-venv"


def advanced_ocr_runtime_python() -> Path:
    root = advanced_ocr_runtime_root()
    if os.name == "nt":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def advanced_ocr_model_folder() -> Path:
    return PATHS.models / "Unlimited-OCR"


def advanced_ocr_runtime_ready() -> bool:
    root = advanced_ocr_runtime_root()
    marker = root / ".audiobookstudio_unlimited_ocr_ready.json"
    model = advanced_ocr_model_folder()
    model_marker = model / ".audiobookstudio_model_verified.json"
    return (
        advanced_ocr_runtime_python().is_file()
        and (PATHS.project_root / "Scripts" / "advanced_ocr_worker.py").is_file()
        and marker.is_file()
        and (model / "config.json").is_file()
        and model_marker.is_file()
    )


def advanced_ocr_runtime_summary() -> str:
    if advanced_ocr_runtime_ready():
        return "Optional Unlimited-OCR runtime and verified model are installed"
    return "Optional Advanced OCR module is not installed"

