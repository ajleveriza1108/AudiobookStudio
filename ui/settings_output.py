from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
)

from core.config import Config


class SettingsOutput(QGroupBox):

    output_selected = Signal(str)

    def __init__(self):

        super().__init__("Output")

        self.config = Config()

        layout = QVBoxLayout(self)

        self.button = QPushButton(

            "Choose Output Folder"

        )

        self.label = QLabel(

            self.config.get(

                "output_folder",

                "Output"

            )

        )

        layout.addWidget(

            self.button

        )

        layout.addWidget(

            self.label

        )

        layout.addStretch()

        self.button.clicked.connect(

            self.select_output

        )

    def select_output(self):

        folder = QFileDialog.getExistingDirectory(

            self,

            "Select Output Folder"

        )

        if not folder:

            return

        self.label.setText(

            folder

        )

        self.output_selected.emit(

            folder

        )

    def current_output(self):

        return self.label.text()

    def set_output(

        self,

        folder

    ):

        self.label.setText(

            folder

        )