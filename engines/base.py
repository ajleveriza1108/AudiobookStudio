from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseEngine(ABC):
    """Stable contract implemented by every Audiobook Studio TTS engine."""

    @abstractmethod
    def speak(
        self,
        text: str,
        output_file: str | Path,
        voice: str,
        speed: float,
        pitch: float,
    ) -> str:
        """Generate one audio chunk and return its final path."""

    @abstractmethod
    def available_voices(self) -> list[str]:
        """Return voice identifiers accepted by speak()."""

    def backend(self) -> str:
        return "Unknown"

    def gpu_name(self) -> str:
        return "Unknown"

    def capabilities(self) -> dict[str, Any]:
        return {
            "voice_cloning": False,
            "multilingual": False,
            "streaming": False,
            "pitch_control": False,
        }

    def health_check(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": self.__class__.__name__,
            "backend": self.backend(),
            "gpu": self.gpu_name(),
            "voices": len(self.available_voices()),
        }

    def unload(self) -> None:
        """Release model and GPU resources. Engines may override this method."""
