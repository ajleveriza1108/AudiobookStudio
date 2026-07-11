import platform
import psutil


class Environment:

    @staticmethod
    def report():

        gpu = "Unknown"
        cuda = "Unavailable"
        torch_version = "Not Loaded"

        try:

            import torch

            torch_version = torch.__version__

            if torch.cuda.is_available():

                gpu = torch.cuda.get_device_name(0)

                cuda = torch.version.cuda

            else:

                gpu = "CPU"

        except Exception:

            gpu = "Unavailable"

        return {

            "python": platform.python_version(),

            "platform": platform.platform(),

            "cpu": platform.processor(),

            "ram": round(

                psutil.virtual_memory().total

                / 1024**3,

                2

            ),

            "gpu": gpu,

            "cuda": cuda,

            "torch": torch_version,

        }