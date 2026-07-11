from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from core.cover import CoverExtractor


class PreviewCover(QLabel):

    def __init__(self):

        super().__init__()

        # ==========================================
        # FIX: Locking the cover size prevents the text below from crushing it
        # ==========================================
        self.setFixedSize(

            260,

            360,

        )

        self.setAlignment(

            Qt.AlignCenter

        )

        self.setStyleSheet("""

background:#111111;

border:1px solid #2A2A2A;

border-radius:16px;

""")

    def load_cover(

        self,

        book,

    ):

        image = Path(book).with_suffix(

            ".png"

        )

        try:

            extractor = CoverExtractor()

            if Path(book).suffix.lower() == ".pdf":

                extractor.pdf(

                    book,

                    image,

                )

            else:

                extractor.epub(

                    book,

                    image,

                )

            if image.exists():

                pix = QPixmap(

                    str(image)

                )

                self.setPixmap(

                    pix.scaled(

                        self.size(),

                        Qt.KeepAspectRatio,

                        Qt.SmoothTransformation,

                    )

                )

            else:

                self.setText(

                    "No Cover"

                )

        except Exception:

            self.setText(

                "No Cover"

            )

    def clear_cover(self):

        self.clear()

        self.setText("")