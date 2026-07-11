from pathlib import Path

from core.parser import extract_book_text
from core.cleaner import clean_text
from core.chunker import split_into_chunks

from core.generator import AudiobookGenerator


BOOK = Path(

    "Books"

) / "Stalking the Wild Pendulum On the Mechanics of Consciousness.pdf"


OUTPUT = Path(

    "Output"

)


def main():

    print(

        "Reading..."

    )

    text = extract_book_text(

        BOOK

    )

    text = clean_text(

        text

    )

    chunks = split_into_chunks(

        text

    )

    print()

    print(

        f"Chunks: {len(chunks)}"

    )

    generator = AudiobookGenerator()

    generator.generate(

        title=BOOK.stem,

        chunks=chunks[:5],

        output_folder=OUTPUT / BOOK.stem,

        voice="af_heart",

        speed=1.0,

        pitch=0

    )

    print()

    print(

        "Done."

    )


if __name__ == "__main__":

    main()