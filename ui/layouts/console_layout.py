from PySide6.QtWidgets import (
    QTextEdit,
    QSizePolicy,
)


class ConsolePanel(QTextEdit):

    def __init__(self):

        super().__init__()

        self.setReadOnly(True)

        self.setMinimumHeight(180)
        self.setMaximumHeight(180)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

    def log(self, text):

        self.append(text)

    def clear_log(self):

        self.clear()