from pathlib import Path
import json
from datetime import datetime


FILE = Path("history.json")


class History:

    def __init__(self):

        self.items = []

        self.load()

    def load(self):

        if FILE.exists():

            with open(

                FILE,

                encoding="utf-8"

            ) as f:

                self.items = json.load(f)

        else:

            self.save()

    def save(self):

        with open(

            FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                self.items,

                f,

                indent=4,

                ensure_ascii=False

            )

    def add(

        self,

        book,

        output,

        duration,

        engine

    ):

        self.items.insert(

            0,

            {

                "book":str(book),

                "output":str(output),

                "duration":duration,

                "engine":engine,

                "time":datetime.now().isoformat()

            }

        )

        self.items = self.items[:500]

        self.save()

    def all(self):

        return self.items