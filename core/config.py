from pathlib import Path
import json


CONFIG_FILE = Path("config.json")


DEFAULT_CONFIG = {

    "engine": "kokoro",

    "voice": "af_heart",

    "speed": 1.0,

    "pitch": 0.0,

    "theme": "dark",

    "output_folder": "Output",

    "window_width": 1850,

    "window_height": 1000,

    "remember_last_book": True,

    "last_book": "",

    "last_books": [],

    "auto_merge": True,

    "delete_chunks": False,

    "export_wav": True,

    "export_mp3": False,

    "export_m4b": False,

    "bitrate": "192k"

}


class Config:

    def __init__(self):

        self.data = DEFAULT_CONFIG.copy()

        self.load()

    def load(self):

        if not CONFIG_FILE.exists():

            self.save()

            return

        try:

            with open(

                CONFIG_FILE,

                "r",

                encoding="utf-8"

            ) as f:

                loaded = json.load(f)

            self.data.update(loaded)

        except Exception:

            self.save()

    def save(self):

        with open(

            CONFIG_FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                self.data,

                f,

                indent=4,

                ensure_ascii=False

            )

    def get(

        self,

        key,

        default=None

    ):

        return self.data.get(

            key,

            default

        )

    def set(

        self,

        key,

        value

    ):

        self.data[key] = value

        self.save()

    def append_recent_book(

        self,

        book

    ):

        book = str(book)

        books = self.data.get(

            "last_books",

            []

        )

        if book in books:

            books.remove(book)

        books.insert(

            0,

            book

        )

        books = books[:20]

        self.data["last_books"] = books

        self.data["last_book"] = book

        self.save()

    def recent_books(self):

        return self.data.get(

            "last_books",

            []
        )