import gc

import torch


class MemoryManager:

    @staticmethod
    def cleanup():

        gc.collect()

        if torch.cuda.is_available():

            torch.cuda.empty_cache()

            torch.cuda.ipc_collect()

    @staticmethod
    def gpu():

        if not torch.cuda.is_available():

            return {

                "allocated": 0,

                "reserved": 0,

                "total": 0,

            }

        prop = torch.cuda.get_device_properties(
            0,
        )

        return {

            "allocated": torch.cuda.memory_allocated(
                0,
            ),

            "reserved": torch.cuda.memory_reserved(
                0,
            ),

            "total": prop.total_memory,

        }

    @staticmethod
    def percent():

        gpu = MemoryManager.gpu()

        if gpu["total"] == 0:

            return 0

        return round(

            gpu["allocated"]

            /

            gpu["total"]

            *

            100,

            2,

        )

    @staticmethod
    def before_chunk():

        MemoryManager.cleanup()

    @staticmethod
    def after_chunk():

        MemoryManager.cleanup()