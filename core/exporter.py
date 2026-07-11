from pathlib import Path
import json
from datetime import datetime


class Exporter:

    def __init__(self):

        pass

    def save_project(

        self,

        folder,

        metadata

    ):

        folder = Path(folder)

        folder.mkdir(

            parents=True,

            exist_ok=True

        )

        metadata["saved"] = datetime.now().isoformat()

        with open(

            folder / "project.json",

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                metadata,

                f,

                indent=4,

                ensure_ascii=False

            )

    def load_project(

        self,

        folder

    ):

        folder = Path(folder)

        file = folder / "project.json"

        if not file.exists():

            return {}

        with open(

            file,

            encoding="utf-8"

        ) as f:

            return json.load(f)

    def export_metadata(

        self,

        folder,

        metadata

    ):

        folder = Path(folder)

        with open(

            folder / "metadata.json",

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                metadata,

                f,

                indent=4,

                ensure_ascii=False

            )

    def export_chapters(

        self,

        folder,

        chapters

    ):

        folder = Path(folder)

        with open(

            folder / "chapters.json",

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                chapters,

                f,

                indent=4,

                ensure_ascii=False

            )