from pathlib import Path

import fitz
from ebooklib import epub


class CoverExtractor:

    def pdf(

        self,

        file,

        output

    ):

        file = Path(file)

        output = Path(output)

        pdf = fitz.open(file)

        page = pdf[0]

        pix = page.get_pixmap(

            dpi=200

        )

        pix.save(output)

        return output

    def epub(

        self,

        file,

        output

    ):

        book = epub.read_epub(file)

        for item in book.items:

            if "cover" in item.get_name().lower():

                output.write_bytes(

                    item.get_content()

                )

                return output

        return None