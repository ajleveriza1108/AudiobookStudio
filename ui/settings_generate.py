from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QPushButton,
)

from ui.layouts.generate_button_style import GenerateButtonStyle


class SettingsGenerate(QGroupBox):

    generate_requested = Signal()

    def __init__(self):

        super().__init__("Generate")

        layout = QVBoxLayout(self)

        self.button = QPushButton(
            "Generate Audiobook"
        )

        self.button.setMinimumHeight(58)

        self.button.clicked.connect(
            self.generate_requested.emit
        )

        layout.addWidget(
            self.button
        )

        self.set_enabled(False)

    def set_enabled(
        self,
        enabled,
    ):

        self.button.setEnabled(
            enabled
        )

        if enabled:

            self.button.setStyleSheet(
                GenerateButtonStyle.ENABLED
            )

        else:

            self.button.setStyleSheet(
                GenerateButtonStyle.DISABLED
            )

    def set_text(
        self,
        text,
    ):

        self.button.setText(
            text
        )

    def enable(self):

        self.set_enabled(
            True
        )

    def disable(self):

        self.set_enabled(
            False
        )