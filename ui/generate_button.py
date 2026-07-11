from PySide6.QtWidgets import QPushButton


class GenerateButton(QPushButton):

    def __init__(self, parent=None):

        super().__init__("Generate Audiobook", parent)

        self.setEnabled(False)

        self.setStyle(False)

    def set_ready(self, state: bool):

        self.setEnabled(state)
        self.setStyle(state)

    def setStyle(self, enabled: bool):

        if enabled:

            self.setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    border-radius: 8px;
                    padding: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)

        else:

            self.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #777;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)