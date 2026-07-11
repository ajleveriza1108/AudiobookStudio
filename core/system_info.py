import platform
import psutil


class SystemInfo:

    @staticmethod
    def gpu():

        try:

            import torch

            if torch.cuda.is_available():

                return {

                    "name": torch.cuda.get_device_name(0),

                    "cuda": torch.version.cuda,

                    "available": True

                }

            return {

                "name": "CPU",

                "cuda": None,

                "available": False

            }

        except Exception:

            return {

                "name": "Unknown",

                "cuda": None,

                "available": False

            }

    @staticmethod
    def cpu():

        return platform.processor()

    @staticmethod
    def ram():

        return round(

            psutil.virtual_memory().total

            /

            1024**3,

            2

        )