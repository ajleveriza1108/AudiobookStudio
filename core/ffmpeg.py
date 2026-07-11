import shutil
import subprocess


class FFmpeg:

    @staticmethod
    def exists():

        return shutil.which("ffmpeg") is not None

    @staticmethod
    def version():

        if not FFmpeg.exists():

            return None

        try:

            result = subprocess.run(

                [

                    "ffmpeg",

                    "-version"

                ],

                capture_output=True,

                text=True

            )

            return result.stdout.splitlines()[0]

        except Exception:

            return None