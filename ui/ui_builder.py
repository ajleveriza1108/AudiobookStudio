from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from ui.central_panel import CentralPanel
from ui.footer import Footer
from ui.header import Header
from ui.workspace import Workspace
from ui.responsive_controller import ResponsiveController


class UIBuilder:
    def __init__(self, window):
        self.window = window

    def build(self):
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(6, 5, 6, 4)
        layout.setSpacing(4)

        self.window.header = Header()
        self.window.central = CentralPanel()
        self.window.workspace = Workspace()
        self.window.footer = Footer()

        self.window.central.console = self.window.workspace.console
        self.window.central.workspace = self.window.workspace

        self.window.content_splitter = QSplitter(Qt.Vertical)
        self.window.content_splitter.setChildrenCollapsible(False)
        self.window.content_splitter.setHandleWidth(4)
        self.window.content_splitter.addWidget(self.window.central)
        self.window.content_splitter.addWidget(self.window.workspace)
        self.window.content_splitter.setStretchFactor(0, 1)
        self.window.content_splitter.setStretchFactor(1, 0)
        self.window.content_splitter.setSizes([650, 220])

        layout.addWidget(self.window.header)
        layout.addWidget(self.window.content_splitter, 1)
        layout.addWidget(self.window.footer)

        self.window.responsive = ResponsiveController(self.window)
