import re


PATTERNS = [

    r"^chapter\s+\d+",

    r"^chapter\s+[ivxlcdm]+",

    r"^book\s+\d+",

    r"^part\s+\d+",

    r"^prologue",

    r"^epilogue",

    r"^\d+\.",

]


def detect_chapters(text):

    chapters = []

    position = 0

    for line in text.splitlines():

        candidate = line.strip()

        lower = candidate.lower()

        for pattern in PATTERNS:

            if re.match(

                pattern,

                lower

            ):

                chapters.append({

                    "title": candidate,

                    "position": position

                })

                break

        position += len(line) + 1

    if not chapters:

        chapters.append({

            "title": "Beginning",

            "position": 0

        })

    return chapters


def split_by_chapters(

    text

):

    chapters = detect_chapters(text)

    if len(chapters) == 1:

        return [text]

    sections = []

    for index in range(len(chapters)):

        start = chapters[index]["position"]

        if index == len(chapters) - 1:

            end = len(text)

        else:

            end = chapters[index + 1]["position"]

        sections.append(

            text[start:end]

        )

    return sections