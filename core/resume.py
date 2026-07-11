from pathlib import Path
import json


class ResumeManager:

    FILE_NAME = "progress.json"

    def __init__(

        self,

        output_folder,

    ):

        self.output = Path(

            output_folder,

        )

        self.file = self.output / self.FILE_NAME

    def exists(self):

        return self.file.exists()

    def save(

        self,

        current_chunk,

        total_chunks,

        current_chapter,

    ):

        self.output.mkdir(

            parents=True,

            exist_ok=True,

        )

        data = {

            "chunk": current_chunk,

            "total": total_chunks,

            "chapter": current_chapter,

        }

        self.file.write_text(

            json.dumps(

                data,

                indent=4,

            ),

            encoding="utf-8",

        )

    def load(self):

        if not self.exists():

            return None

        return json.loads(

            self.file.read_text(

                encoding="utf-8",

            )

        )

    def clear(self):

        if self.exists():

            self.file.unlink()