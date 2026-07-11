from engines.base import BaseEngine


class XTTSEngine(BaseEngine):

    def __init__(self):

        self.ready = False

    def speak(

        self,

        text,

        output_file,

        voice,

        speed,

        pitch

    ):

        raise NotImplementedError(

            "XTTS support is not installed."

        )

    def available_voices(self):

        return []

    def backend(self):

        return "CUDA"

    def gpu_name(self):

        return "N/A"