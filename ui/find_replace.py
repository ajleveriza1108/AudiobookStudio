from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
)


class FindReplace(QWidget):

    applied = Signal(dict)

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel(

            "Find && Replace"

        )

        title.setStyleSheet("""

font-size:20px;

font-weight:bold;

""")

        layout.addWidget(title)

        info = QLabel(

            "One replacement per line.\nExample:\nAI=Artificial Intelligence"

        )

        layout.addWidget(info)

        self.editor = QTextEdit()

        layout.addWidget(

            self.editor,

            1

        )

        self.apply = QPushButton(

            "Apply"

        )

        layout.addWidget(

            self.apply

        )

        self.apply.clicked.connect(

            self.save_rules

        )

    def save_rules(self):

        rules = {}

        for line in self.editor.toPlainText().splitlines():

            if "=" not in line:

                continue

            left, right = line.split(

                "=",

                1

            )

            rules[left.strip()] = right.strip()

        self.applied.emit(

            rules

        )