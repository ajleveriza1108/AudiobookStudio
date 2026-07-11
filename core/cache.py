from pathlib import Path
import hashlib
import json


class CacheManager:

    FILE_NAME = "cache.json"

    def __init__(self, folder):

        self.folder = Path(folder)
        self.folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.file = self.folder / self.FILE_NAME

        self.data = {}

        self.load()

    def load(self):

        if not self.file.exists():
            return

        try:

            self.data = json.loads(
                self.file.read_text(
                    encoding="utf-8",
                )
            )

        except Exception:

            self.data = {}

    def save(self):

        self.file.write_text(
            json.dumps(
                self.data,
                indent=4,
            ),
            encoding="utf-8",
        )

    def hash_text(self, text):

        return hashlib.sha256(
            text.encode(
                "utf-8",
            )
        ).hexdigest()

    def contains(self, text):

        return self.hash_text(text) in self.data

    def add(self, text, wav):

        self.data[
            self.hash_text(text)
        ] = str(wav)

        self.save()

    def wav(self, text):

        return self.data.get(
            self.hash_text(text),
        )

    def clear(self):

        self.data = {}

        if self.file.exists():

            self.file.unlink()