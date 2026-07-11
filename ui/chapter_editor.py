from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
)


class ChapterEditor(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel(

            "Chapter Editor"

        )

        title.setStyleSheet("""

font-size:20px;

font-weight:bold;

""")

        layout.addWidget(title)

        self.list = QListWidget()

        layout.addWidget(

            self.list,

            1

        )

        self.refresh = QPushButton(

            "Reload Chapters"

        )

        layout.addWidget(

            self.refresh

        )

    def load(

        self,

        chapters

    ):

        self.list.clear()

        for chapter in chapters:

            self.list.addItem(

                chapter["title"]

            )