from pathlib import Path
import json
import hashlib
from datetime import datetime


DATABASE = Path("library.json")


class Library:

    def __init__(self):

        self.books = []

        self.load()

    def load(self):

        if DATABASE.exists():

            try:

                with open(

                    DATABASE,

                    "r",

                    encoding="utf-8"

                ) as f:

                    self.books = json.load(f)

            except Exception:

                self.books = []

        else:

            self.save()

    def save(self):

        with open(

            DATABASE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                self.books,

                f,

                indent=4,

                ensure_ascii=False

            )

    def checksum(self,file):

        h=hashlib.sha256()

        with open(file,"rb") as f:

            while True:

                block=f.read(1024*1024)

                if not block:

                    break

                h.update(block)

        return h.hexdigest()

    def add(self,file):

        file=Path(file)

        checksum=self.checksum(file)

        for book in self.books:

            if book["checksum"]==checksum:

                return False

        self.books.append({

            "title":file.stem,

            "path":str(file),

            "checksum":checksum,

            "favorite":False,

            "created":datetime.now().isoformat(),

            "last_opened":None,

            "completed":False,

            "progress":0,

            "engine":"kokoro",

            "voice":"af_heart",

            "tags":[]

        })

        self.save()

        return True

    def remove(self,path):

        self.books=[

            x for x in self.books

            if x["path"]!=str(path)

        ]

        self.save()

    def update_progress(

        self,

        path,

        percent

    ):

        for book in self.books:

            if book["path"]==str(path):

                book["progress"]=percent

                if percent>=100:

                    book["completed"]=True

                break

        self.save()

    def touch(self,path):

        for book in self.books:

            if book["path"]==str(path):

                book["last_opened"]=datetime.now().isoformat()

                break

        self.save()

    def favorite(self,path):

        for book in self.books:

            if book["path"]==str(path):

                book["favorite"]=not book["favorite"]

                break

        self.save()

    def search(self,text):

        text=text.lower()

        return [

            b for b in self.books

            if text in b["title"].lower()

        ]

    def all(self):

        return self.books

    def recent(self):

        return sorted(

            self.books,

            key=lambda x:

            x["last_opened"]

            or "",

            reverse=True

        )

    def completed(self):

        return [

            b for b in self.books

            if b["completed"]

        ]

    def unfinished(self):

        return [

            b for b in self.books

            if not b["completed"]

        ]