from __future__ import annotations

from engines.factory import EngineFactory


class EngineService:
    """Shared lazy-loaded engine service used by the GUI and workers."""

    _factory = EngineFactory()
    _engine = None
    _engine_name: str | None = None

    @classmethod
    def load(cls, engine_name: str = "kokoro"):
        requested = str(engine_name or "kokoro").strip().lower()

        if cls._engine is None or cls._engine_name != requested:
            cls._engine = cls._factory.load(requested)
            cls._engine_name = cls._factory.current_name() or requested

        return cls._engine

    @classmethod
    def unload(cls) -> None:
        cls._factory.unload()
        cls._engine = None
        cls._engine_name = None

    @classmethod
    def current(cls):
        return cls._engine

    @classmethod
    def current_name(cls) -> str | None:
        return cls._engine_name

    @classmethod
    def loaded(cls) -> bool:
        return cls._engine is not None

    @classmethod
    def voices(cls, engine_name: str | None = None) -> list[str]:
        if engine_name:
            engine = cls.load(engine_name)
            return list(engine.available_voices())

        if cls._engine is None:
            return []

        return list(cls._engine.available_voices())

    @classmethod
    def speak(
        cls,
        text,
        output,
        voice,
        speed,
        pitch,
        engine_name: str = "kokoro",
    ):
        engine = cls.load(engine_name)
        return engine.speak(
            text=text,
            output_file=output,
            voice=voice,
            speed=speed,
            pitch=pitch,
        )

    @classmethod
    def backend(cls) -> str:
        if cls._engine is None:
            return "Not Loaded"
        return str(cls._engine.backend())

    @classmethod
    def gpu(cls) -> str:
        if cls._engine is None:
            return "Not Loaded"
        return str(cls._engine.gpu_name())
