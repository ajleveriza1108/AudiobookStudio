from pathlib import Path
import json
from datetime import datetime


class ProgressManager:

    FILE_NAME = "progress.json"

    def __init__(

        self,

        project_folder,

    ):

        self.project_folder = Path(

            project_folder,

        )

        self.file = self.project_folder / self.FILE_NAME

    def load(self):

        if not self.file.exists():

            return None

        try:

            return json.loads(

                self.file.read_text(

                    encoding="utf-8",

                )

            )

        except Exception:

            return None

    def save(

        self,

        chunk,

        total,

        chapter,

        wav,

    ):

        self.project_folder.mkdir(

            parents=True,

            exist_ok=True,

        )

        data = {

            "chunk": chunk,

            "total": total,

            "chapter": chapter,

            "wav": str(

                wav,

            ),

            "updated": datetime.now().isoformat(),

        }

        self.file.write_text(

            json.dumps(

                data,

                indent=4,

            ),

            encoding="utf-8",

        )

    def clear(self):

        if self.file.exists():

            self.file.unlink()