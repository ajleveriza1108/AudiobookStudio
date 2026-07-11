from pathlib import Path


FOLDERS = [

    "Books",

    "Output",

    "Logs",

    "Models",

    "Scripts",

    "Temp",

    "Voices",

]


def initialize():

    for folder in FOLDERS:

        Path(folder).mkdir(

            parents=True,

            exist_ok=True

        )