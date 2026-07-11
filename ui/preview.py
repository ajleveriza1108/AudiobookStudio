from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)

from core.parser import parse_book
from core.parser import extract_book_text
from core.cleaner import clean_text
from core.chapters import detect_chapters
from core.estimate import estimate_duration
from core.engine_service import EngineService

from ui.preview_cover import PreviewCover
from ui.preview_metadata import PreviewMetadata
from ui.preview_text import PreviewText


class PreviewPanel(QWidget):

    def __init__(self):

        super().__init__()

        self.current_book = None

        self.build_ui()

    def build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(

            12,

            12,

            12,

            12,

        )

        root.setSpacing(

            12

        )

        self.title = QLabel(

            "No Book Selected"

        )

        self.title.setAlignment(

            Qt.AlignCenter

        )

        self.title.setStyleSheet("""

font-size:24px;

font-weight:bold;

padding:6px;

""")

        # ==========================================
        # FIX: Allow title to wrap and expand
        # ==========================================
        self.title.setWordWrap(True)
        
        self.title.setMinimumHeight(60)

        self.title.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum
        )

        root.addWidget(

            self.title

        )

        top = QHBoxLayout()

        top.setSpacing(

            12

        )

        root.addLayout(

            top,

            1

        )

        self.cover = PreviewCover()

        top.addWidget(

            self.cover

        )

        self.meta = PreviewMetadata()

        top.addWidget(

            self.meta,

            1

        )

        self.preview = PreviewText()

        root.addWidget(

            self.preview,

            2

        )

    def load_book(

        self,

        file,

    ):

        self.current_book = Path(

            file

        )

        # ==========================================
        # FIX: Fallback title to prevent blank UI
        # ==========================================
        self.title.setText(

            self.current_book.stem

        )

        # ==========================================
        # FIX: Safe Metadata Parsing
        # ==========================================
        try:

            meta = parse_book(

                file

            )

            self.title.setText(

                meta.get("title", self.current_book.stem)

            )

            self.meta.set_value(

                "Author",

                meta.get("author", "Unknown")

            )

            self.meta.set_value(

                "Pages",

                meta.get("pages", "Unknown")

            )

            self.meta.set_value(

                "Language",

                meta.get("language", "Unknown")

            )

            self.meta.set_value(

                "Type",

                meta.get("type", "Unknown")

            )

        except Exception as e:

            print(

                f"Metadata parsing error: {e}"

            )

        # ==========================================
        # FIX: Safe Text Parsing
        # ==========================================
        try:

            text = extract_book_text(

                file

            )

            text = clean_text(

                text

            )

            chapters = detect_chapters(

                text

            )

            hours, minutes = estimate_duration(

                text

            )

            self.meta.set_value(

                "Duration",

                f"{hours}h {minutes}m"

            )

            self.meta.set_value(

                "Words",

                f"{len(text.split()):,}"

            )

            self.meta.set_value(

                "Characters",

                f"{len(text):,}"

            )

            self.meta.set_value(

                "Chapters",

                len(chapters)

            )

            self.meta.set_value(

                "Estimated Size",

                f"{round(minutes*1.45,1)} MB"

            )

            self.preview.set_text(

                text[:8000]

            )

        except Exception as e:

            print(

                f"Text parsing error: {e}"

            )

            self.preview.set_text(

                "Unable to extract or preview text for this book."

            )

        self.meta.set_value(

            "Engine",

            "Kokoro"

        )

        if EngineService.loaded():

            backend = EngineService.backend()

        else:

            backend = "Not Loaded"

        self.meta.set_value(

            "Backend",

            backend

        )

        self.meta.set_value(

            "Output",

            "Output"

        )

        self.cover.load_cover(

            self.current_book

        )

    def clear(self):

        self.title.setText(

            "No Book Selected"

        )

        self.meta.clear_values()

        self.preview.clear_text()

        self.cover.clear_cover()