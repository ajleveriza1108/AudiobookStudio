from __future__ import annotations

from threading import RLock
from typing import Any

from engines.manager import EngineManager


class EngineFactory:
    """Loads one TTS engine at a time and releases the previous model safely."""

    def __init__(self, manager: EngineManager | None = None) -> None:
        self.manager = manager or EngineManager()
        self._engine = None
        self._engine_name: str | None = None
        self._lock = RLock()

    def load(self, name: str = "kokoro", force_reload: bool = False):
        requested = str(name or "kokoro").strip().lower()
        if requested not in self.manager.names():
            requested = "kokoro"

        with self._lock:
            if (
                not force_reload
                and self._engine is not None
                and self._engine_name == requested
            ):
                return self._engine

            self.unload()
            self._engine = self.manager.create(requested)
            self._engine_name = requested
            return self._engine

    def unload(self) -> None:
        with self._lock:
            engine = self._engine
            self._engine = None
            self._engine_name = None

            if engine is not None:
                unload = getattr(engine, "unload", None)
                if callable(unload):
                    try:
                        unload()
                    except Exception:
                        pass

    def current(self):
        return self._engine

    def current_name(self) -> str | None:
        return self._engine_name

    def voices(self) -> list[str]:
        if self._engine is None:
            return []
        return list(self._engine.available_voices())

    def backend(self) -> str:
        if self._engine is None:
            return "Not Loaded"
        return str(self._engine.backend())

    def gpu(self) -> str:
        if self._engine is None:
            return "Not Loaded"
        return str(self._engine.gpu_name())

    def capabilities(self) -> dict[str, Any]:
        if self._engine is None:
            return {}

        method = getattr(self._engine, "capabilities", None)
        if callable(method):
            return dict(method())

        if self._engine_name:
            return dict(
                self.manager.manifest(self._engine_name).capabilities
            )

        return {}

    def health(self) -> dict[str, Any]:
        if self._engine is None:
            return {"ok": False, "reason": "No engine loaded"}

        method = getattr(self._engine, "health_check", None)
        if callable(method):
            return dict(method())

        return {
            "ok": True,
            "engine": self._engine_name,
            "backend": self.backend(),
            "gpu": self.gpu(),
        }
