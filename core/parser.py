from pathlib import Path

import fitz
from ebooklib import epub
from bs4 import BeautifulSoup


SUPPORTED = [

    ".pdf",

    ".epub"

]


def parse_book(book):

    book = Path(book)

    suffix = book.suffix.lower()

    if suffix == ".pdf":

        return parse_pdf(book)

    if suffix == ".epub":

        return parse_epub(book)

    raise RuntimeError(

        f"Unsupported format: {suffix}"

    )


def parse_pdf(book):

    pdf = fitz.open(book)

    metadata = pdf.metadata

    return {

        "title":

            metadata.get("title")

            or book.stem,

        "author":

            metadata.get("author")

            or "Unknown",

        "pages":

            pdf.page_count,

        "language":

            metadata.get("language")

            or "Unknown",

        "type":"PDF"

    }


def parse_epub(book):

    epub_book = epub.read_epub(book)

    title = "Unknown"

    author = "Unknown"

    language = "Unknown"

    try:

        title = epub_book.get_metadata(

            "DC",

            "title"

        )[0][0]

    except:

        pass

    try:

        author = epub_book.get_metadata(

            "DC",

            "creator"

        )[0][0]

    except:

        pass

    try:

        language = epub_book.get_metadata(

            "DC",

            "language"

        )[0][0]

    except:

        pass

    return {

        "title":title,

        "author":author,

        "pages":"Unknown",

        "language":language,

        "type":"EPUB"

    }


def extract_book_text(book):

    book = Path(book)

    if book.suffix.lower()==".pdf":

        return extract_pdf(book)

    if book.suffix.lower()==".epub":

        return extract_epub(book)

    raise RuntimeError("Unsupported")


def extract_pdf(book):

    pdf = fitz.open(book)

    pages=[]

    for page in pdf:

        try:

            pages.append(

                page.get_text()

            )

        except:

            pass

    return "\n".join(pages)


def extract_epub(book):

    epub_book = epub.read_epub(book)

    text=[]

    for item in epub_book.get_items():

        if item.get_type()==9:

            soup=BeautifulSoup(

                item.get_content(),

                "html.parser"

            )

            text.append(

                soup.get_text(

                    "\n"

                )

            )

    return "\n".join(text)


def extract_cover(book):

    try:

        epub_book=epub.read_epub(book)

        for item in epub_book.items:

            if "cover" in item.get_name().lower():

                return item.get_content()

    except:

        pass

    return None


def page_count(book):

    if Path(book).suffix.lower()==".pdf":

        return fitz.open(book).page_count

    return 0