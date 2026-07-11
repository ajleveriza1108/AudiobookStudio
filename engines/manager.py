import importlib


class EngineManager:

    def __init__(self):

        self.engines = {

            "kokoro": (

                "engines.kokoro",

                "KokoroEngine",

            ),

            "piper": (

                "engines.piper",

                "PiperEngine",

            ),

            "xtts": (

                "engines.xtts",

                "XTTSEngine",

            ),

        }

    def names(self):

        return list(

            self.engines.keys()

        )

    def create(

        self,

        name,

    ):

        name = name.lower()

        if name not in self.engines:

            name = "kokoro"

        module_name, class_name = self.engines[name]

        module = importlib.import_module(

            module_name

        )

        engine_class = getattr(

            module,

            class_name

        )

        return engine_class()

    def available(self):

        available = []

        for name in self.names():

            try:

                engine = self.create(

                    name

                )

                available.append(

                    {

                        "name": name,

                        "backend": engine.backend(),

                        "gpu": engine.gpu_name(),

                    }

                )

            except Exception:

                available.append(

                    {

                        "name": name,

                        "backend": "Unavailable",

                        "gpu": "Unavailable",

                    }

                )

        return available