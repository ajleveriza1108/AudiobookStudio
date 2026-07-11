from datetime import datetime
from pathlib import Path


class Logger:

    def __init__(self, folder="Logs"):

        self.folder = Path(folder)

        self.folder.mkdir(

            parents=True,

            exist_ok=True,

        )

        self.file = self.folder / "audiobook.log"

    def _write(

        self,

        level,

        message,

    ):

        now = datetime.now().strftime(

            "%Y-%m-%d %H:%M:%S"

        )

        line = f"[{now}] [{level}] {message}\n"

        with open(

            self.file,

            "a",

            encoding="utf-8",

        ) as f:

            f.write(

                line

            )

    def info(

        self,

        message,

    ):

        self._write(

            "INFO",

            message,

        )

    def warning(

        self,

        message,

    ):

        self._write(

            "WARNING",

            message,

        )

    def error(

        self,

        message,

    ):

        self._write(

            "ERROR",

            message,

        )

    def success(

        self,

        message,

    ):

        self._write(

            "SUCCESS",

            message,

        )

    def separator(self):

        self._write(

            "-----",

            "-" * 70,

        )