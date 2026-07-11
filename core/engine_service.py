from engines.factory import EngineFactory


class EngineService:

    _factory = EngineFactory()

    _engine = None

    @classmethod
    def load(cls, engine_name="kokoro"):

        if cls._engine is None:

            cls._engine = cls._factory.load(

                engine_name

            )

        return cls._engine

    @classmethod
    def unload(cls):

        cls._engine = None

    @classmethod
    def current(cls):

        return cls._engine

    @classmethod
    def loaded(cls):

        return cls._engine is not None

    @classmethod
    def voices(cls):

        if cls._engine is None:

            return []

        return cls._engine.available_voices()

    @classmethod
    def speak(

        cls,

        text,

        output,

        voice,

        speed,

        pitch

    ):

        if cls._engine is None:

            cls.load()

        return cls._engine.speak(

            text=text,

            output_file=output,

            voice=voice,

            speed=speed,

            pitch=pitch

        )

    @classmethod
    def backend(cls):

        if cls._engine is None:

            return "Not Loaded"

        return cls._engine.backend()

    @classmethod
    def gpu(cls):

        if cls._engine is None:

            return "Not Loaded"

        return cls._engine.gpu_name()