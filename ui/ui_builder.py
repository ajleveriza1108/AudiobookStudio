from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from ui.header import Header
from ui.central_panel import CentralPanel
from ui.workspace import Workspace
from ui.footer import Footer


class UIBuilder:

    def __init__(self, window):

        self.window = window

    def build(self):

        central = QWidget()

        self.window.setCentralWidget(

            central

        )

        layout = QVBoxLayout(

            central

        )

        layout.setContentsMargins(

            12,

            12,

            12,

            12,

        )

        layout.setSpacing(

            10

        )

        self.window.header = Header()

        self.window.central = CentralPanel()

        self.window.workspace = Workspace()

        self.window.footer = Footer()

        layout.addWidget(

            self.window.header,

            0,

        )

        #
        # Central panel should always dominate.
        #

        layout.addWidget(

            self.window.central,

            8,

        )

        #
        # Workspace keeps a constant visual size
        # whether windowed or maximized.
        #

        layout.addWidget(

            self.window.workspace,

            2,

        )

        layout.addWidget(

            self.window.footer,

            0,

        )