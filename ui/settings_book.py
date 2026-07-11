from pathlib import Path

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
)


class SettingsBook(QGroupBox):

    book_selected = Signal(str)

    def __init__(self):

        super().__init__("Book")

        layout = QVBoxLayout(self)

        self.button = QPushButton(

            "Import PDF / EPUB"

        )

        self.label = QLabel(

            "No book selected"

        )

        # ==========================================
        # FIX: Allow Book label to wrap instead of crop
        # ==========================================
        self.label.setWordWrap(True)
        
        self.label.setMinimumHeight(30)

        layout.addWidget(

            self.button

        )

        layout.addWidget(

            self.label

        )

        layout.addStretch()

        self.button.clicked.connect(

            self.select_book

        )

    def select_book(self):

        file, _ = QFileDialog.getOpenFileName(

            self,

            "Select Book",

            "",

            "Books (*.pdf *.epub)"

        )

        if not file:

            return

        self.label.setText(

            Path(file).name

        )

        self.book_selected.emit(

            file

        )

    def current_book(self):

        text = self.label.text()

        if text == "No book selected":

            return None

        return text

    def set_book(self, file):

        self.label.setText(

            Path(file).name

        )