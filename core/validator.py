from pathlib import Path


SUPPORTED = [

    ".pdf",

    ".epub"

]


def validate_book(book):

    book = Path(book)

    if not book.exists():

        raise FileNotFoundError(

            str(book)

        )

    if book.suffix.lower() not in SUPPORTED:

        raise RuntimeError(

            "Unsupported file."

        )

    return True


def validate_output(folder):

    folder = Path(folder)

    folder.mkdir(

        parents=True,

        exist_ok=True

    )

    return True