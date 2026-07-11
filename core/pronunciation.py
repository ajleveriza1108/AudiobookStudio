import json
from pathlib import Path


FILE = Path("pronunciation.json")


class PronunciationDictionary:

    def __init__(self):

        self.words = {}

        self.load()

    def load(self):

        if FILE.exists():

            with open(

                FILE,

                encoding="utf-8"

            ) as f:

                self.words = json.load(f)

        else:

            self.save()

    def save(self):

        with open(

            FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                self.words,

                f,

                indent=4,

                ensure_ascii=False

            )

    def replace(

        self,

        text

    ):

        for source, target in self.words.items():

            text = text.replace(

                source,

                target

            )

        return text

    def add(

        self,

        source,

        target

    ):

        self.words[source] = target

        self.save()