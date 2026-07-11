import re


HEADER_PATTERNS=[

    r"^\d+$",

    r"^page\s+\d+$",

    r"^copyright",

    r"^isbn",

    r"^printed in",

    r"^all rights reserved",

]


def clean_text(text):

    text=text.replace("\r","")

    text=text.replace("\t"," ")

    text=text.replace("\x00","")

    text=text.replace("\ufeff","")

    text=text.replace("-\n","")

    text=text.replace("\n"," ")

    text=re.sub(

        r"\s+",

        " ",

        text

    )

    lines=[]

    for line in text.split(". "):

        keep=True

        lower=line.strip().lower()

        for pattern in HEADER_PATTERNS:

            if re.match(

                pattern,

                lower

            ):

                keep=False

                break

        if keep:

            lines.append(

                line.strip()

            )

    text=". ".join(lines)

    text=re.sub(

        r"\[[^\]]+\]",

        "",

        text

    )

    text=re.sub(

        r"\([Pp]age.*?\)",

        "",

        text

    )

    text=re.sub(

        r"\s+",

        " ",

        text

    )

    return text.strip()


def preview(text,length=5000):

    return text[:length]


def character_count(text):

    return len(text)


def word_count(text):

    return len(text.split())