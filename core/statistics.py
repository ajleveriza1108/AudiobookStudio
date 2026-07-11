from pathlib import Path

from core.audio_info import folder_duration
from core.utils import folder_size


class Statistics:

    @staticmethod
    def audiobook(folder):

        folder = Path(folder)

        return {

            "duration":

                folder_duration(folder),

            "size":

                folder_size(folder),

            "chunks":

                len(

                    list(

                        folder.glob(

                            "chunk_*.wav"

                        )

                    )

                )

        }