from engines.manager import EngineManager


class EngineFactory:

    def __init__(self):

        self.manager = EngineManager()

        self._engine = None

        self._engine_name = None

    def load(

        self,

        name="kokoro",

    ):

        name = name.lower()

        if (

            self._engine is not None

            and

            self._engine_name == name

        ):

            return self._engine

        self._engine = self.manager.create(

            name

        )

        self._engine_name = name

        return self._engine

    def unload(self):

        self._engine = None

        self._engine_name = None

    def current(self):

        return self._engine

    def current_name(self):

        return self._engine_name

    def voices(self):

        if self._engine is None:

            return []

        return self._engine.available_voices()

    def backend(self):

        if self._engine is None:

            return "Not Loaded"

        return self._engine.backend()

    def gpu(self):

        if self._engine is None:

            return "Not Loaded"

        return self._engine.gpu_name()