from pathlib import Path
import json


BOOKMARK_FILE = Path("bookmarks.json")


class Bookmarks:

    def __init__(self):

        self.data = {}

        self.load()

    def load(self):

        if BOOKMARK_FILE.exists():

            with open(

                BOOKMARK_FILE,

                encoding="utf-8"

            ) as f:

                self.data = json.load(f)

        else:

            self.save()

    def save(self):

        with open(

            BOOKMARK_FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                self.data,

                f,

                indent=4,

                ensure_ascii=False

            )

    def save_position(

        self,

        book,

        chunk

    ):

        self.data[str(book)] = chunk

        self.save()

    def position(

        self,

        book

    ):

        return self.data.get(

            str(book),

            0

        )

    def remove(

        self,

        book

    ):

        if str(book) in self.data:

            del self.data[str(book)]

            self.save()