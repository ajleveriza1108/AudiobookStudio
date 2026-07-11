from pathlib import Path
import wave


class ChunkValidator:

    @staticmethod
    def exists(

        file,

    ):

        return Path(

            file,

        ).exists()

    @staticmethod
    def valid(

        file,

    ):

        file = Path(

            file,

        )

        if not file.exists():

            return False

        try:

            with wave.open(

                str(file),

                "rb",

            ) as wav:

                if wav.getnframes() <= 0:

                    return False

        except Exception:

            return False

        return file.stat().st_size > 4096

    @staticmethod
    def remove_invalid(

        file,

    ):

        file = Path(

            file,

        )

        if not file.exists():

            return

        if not ChunkValidator.valid(

            file,

        ):

            file.unlink()