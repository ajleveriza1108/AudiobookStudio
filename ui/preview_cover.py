from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel, QSizePolicy

from core.paths import PATHS


class PreviewCover(QLabel):
    """Paint-stable document tile used in the book overview.

    Cover artwork remains disabled in this stability build. The module-level
    PATHS symbol is intentionally retained as a compatibility injection point
    for older integrations and regression tests. No image decoding, pixmap,
    timer, resize callback, or custom paint operation is performed.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("coverPanel")
        self.setMinimumSize(170, 235)
        self.setMaximumSize(220, 310)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self._source: Path | None = None
        self._last_error = ""
        self._show_empty_tile()

    def sizeHint(self) -> QSize:
        return QSize(190, 265)

    def minimumSizeHint(self) -> QSize:
        return QSize(170, 235)

    def _show_empty_tile(self) -> None:
        self.setText("No Book\nSelected")
        self.setToolTip("")

    def load_cover(self, book) -> bool:
        self._source = Path(book).expanduser().resolve()
        self._last_error = ""

        # Missing or moved sources are nonfatal. Preserve the legacy "No Cover"
        # result expected by older callers while keeping the rest of the book
        # workflow available.
        if not self._source.is_file():
            self.setText("No Cover")
            self.setToolTip(f"Book source is unavailable:\n{self._source}")
            return False

        suffix = self._source.suffix.lower()
        if suffix == ".pdf":
            kind = "PDF\nDocument"
        elif suffix == ".epub":
            kind = "EPUB\nE-book"
        else:
            kind = "Book\nDocument"
        self.setText(kind)
        self.setToolTip(
            f"{self._source}\n\n"
            "Cover artwork is temporarily disabled in the stability build. "
            "Book text, OCR, chapters, narration, and export remain available."
        )
        return False

    def clear_cover(self):
        self._source = None
        self._last_error = ""
        self._show_empty_tile()

    def last_error(self) -> str:
        return self._last_error
