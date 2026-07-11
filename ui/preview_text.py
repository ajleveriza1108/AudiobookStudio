from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
)


class PreviewText(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        layout.setContentsMargins(

            0,

            0,

            0,

            0,

        )

        layout.setSpacing(

            8

        )

        title = QLabel(

            "Book Preview"

        )

        title.setStyleSheet("""

font-size:18px;

font-weight:bold;

padding:4px;

""")

        layout.addWidget(

            title

        )

        self.editor = QTextEdit()

        self.editor.setReadOnly(

            True

        )

        self.editor.setPlaceholderText(

            "Import a PDF or EPUB to preview its contents."

        )

        self.editor.setStyleSheet("""

QTextEdit{

background:#101010;

border:1px solid #2A2A2A;

border-radius:14px;

padding:12px;

}

""")

        layout.addWidget(

            self.editor,

            1

        )

    def set_text(

        self,

        text,

    ):

        self.editor.setPlainText(

            text

        )

    def append(

        self,

        text,

    ):

        self.editor.append(

            text

        )

    def clear_text(self):

        self.editor.clear()

    def text(self):

        return self.editor.toPlainText()