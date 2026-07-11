from PySide6.QtWidgets import QProgressBar


class ProgressBar(QProgressBar):

    def __init__(self):

        super().__init__()

        self.setValue(0)