from abc import ABC
from abc import abstractmethod


class BaseEngine(ABC):

    @abstractmethod
    def speak(

        self,

        text,

        output_file,

        voice,

        speed,

        pitch

    ):

        pass

    @abstractmethod
    def available_voices(self):

        pass

    @abstractmethod
    def backend(self):

        pass

    @abstractmethod
    def gpu_name(self):

        pass