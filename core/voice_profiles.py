from pathlib import Path
import json


VOICE_FILE = Path("voices.json")


DEFAULT = {

    "Default":{

        "engine":"kokoro",

        "voice":"af_heart",

        "speed":1.0,

        "pitch":0

    }

}


class VoiceProfiles:

    def __init__(self):

        self.data = {}

        self.load()

    def load(self):

        if not VOICE_FILE.exists():

            self.data = DEFAULT.copy()

            self.save()

            return

        try:

            with open(

                VOICE_FILE,

                "r",

                encoding="utf-8"

            ) as f:

                self.data = json.load(f)

        except Exception:

            self.data = DEFAULT.copy()

            self.save()

    def save(self):

        with open(

            VOICE_FILE,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                self.data,

                f,

                indent=4,

                ensure_ascii=False

            )

    def names(self):

        return sorted(

            self.data.keys()

        )

    def add(

        self,

        name,

        engine,

        voice,

        speed,

        pitch

    ):

        self.data[name] = {

            "engine":engine,

            "voice":voice,

            "speed":speed,

            "pitch":pitch

        }

        self.save()

    def remove(

        self,

        name

    ):

        if name == "Default":

            return

        if name in self.data:

            del self.data[name]

            self.save()

    def get(

        self,

        name

    ):

        return self.data.get(

            name,

            DEFAULT["Default"]

        )