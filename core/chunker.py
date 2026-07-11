import re


DEFAULT_TARGET = 900
DEFAULT_MIN = 500
DEFAULT_MAX = 1400


def normalize(text):

    text = re.sub(

        r"\r",

        "",

        text

    )

    text = re.sub(

        r"\n{2,}",

        "\n\n",

        text

    )

    text = re.sub(

        r"[ \t]+",

        " ",

        text

    )

    return text.strip()


def split_sentences(text):

    pattern = re.compile(

        r"(?<=[.!?])\s+"

    )

    sentences = pattern.split(text)

    cleaned = []

    for sentence in sentences:

        sentence = sentence.strip()

        if sentence:

            cleaned.append(sentence)

    return cleaned


def split_into_chunks(

    text,

    target_size=DEFAULT_TARGET,

    min_size=DEFAULT_MIN,

    max_size=DEFAULT_MAX,

):

    text = normalize(text)

    paragraphs = [

        p.strip()

        for p in text.split("\n\n")

        if p.strip()

    ]

    chunks = []

    current = ""

    for paragraph in paragraphs:

        if len(paragraph) > max_size:

            sentences = split_sentences(

                paragraph

            )

            for sentence in sentences:

                if len(current) + len(sentence) <= target_size:

                    current += sentence + " "

                else:

                    if len(current.strip()) >= min_size:

                        chunks.append(

                            current.strip()

                        )

                        current = ""

                    if len(sentence) > max_size:

                        words = sentence.split()

                        piece = ""

                        for word in words:

                            if len(piece) + len(word) < target_size:

                                piece += word + " "

                            else:

                                chunks.append(

                                    piece.strip()

                                )

                                piece = word + " "

                        if piece:

                            current = piece

                    else:

                        current = sentence + " "

        else:

            if len(current) + len(paragraph) <= target_size:

                current += paragraph + "\n\n"

            else:

                if current.strip():

                    chunks.append(

                        current.strip()

                    )

                current = paragraph + "\n\n"

    if current.strip():

        chunks.append(

            current.strip()

        )

    return chunks


def estimate_chunks(

    text,

    target_size=DEFAULT_TARGET

):

    return max(

        1,

        len(text) // target_size

    )


def average_chunk_size(chunks):

    if not chunks:

        return 0

    total = sum(

        len(chunk)

        for chunk in chunks

    )

    return total // len(chunks)


def statistics(chunks):

    if not chunks:

        return {

            "chunks": 0,

            "largest": 0,

            "smallest": 0,

            "average": 0

        }

    sizes = [

        len(chunk)

        for chunk in chunks

    ]

    return {

        "chunks": len(chunks),

        "largest": max(sizes),

        "smallest": min(sizes),

        "average": sum(sizes) // len(sizes)

    }


if __name__ == "__main__":

    sample = """

Chapter One

This is a short paragraph.

This is another paragraph. It contains several sentences. It should remain together whenever possible. The chunker should avoid cutting in awkward places.

""" * 40

    chunks = split_into_chunks(sample)

    print(

        statistics(chunks)

    )