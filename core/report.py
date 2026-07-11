from pathlib import Path
from datetime import datetime


class GenerationReport:

    def __init__(self):

        self.items = []

        self.started = datetime.now()

    def add(

        self,

        title,

        duration,

        size,

        status

    ):

        self.items.append({

            "title": title,

            "duration": duration,

            "size": size,

            "status": status

        })

    def save(

        self,

        folder

    ):

        folder = Path(folder)

        folder.mkdir(

            parents=True,

            exist_ok=True

        )

        report = folder / "Generation Report.txt"

        with open(

            report,

            "w",

            encoding="utf-8"

        ) as f:

            f.write(

                "Audiobook Studio\n"

            )

            f.write(

                "=" * 70

            )

            f.write("\n\n")

            f.write(

                f"Started : {self.started}\n\n"

            )

            for item in self.items:

                f.write(

                    f"{item['title']}\n"

                )

                f.write(

                    f"Status   : {item['status']}\n"

                )

                f.write(

                    f"Duration : {item['duration']}\n"

                )

                f.write(

                    f"Size     : {item['size']}\n"

                )

                f.write("\n")

            f.write("=" * 70)