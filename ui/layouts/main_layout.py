from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter


class MainLayout(QSplitter):
    def __init__(self, sidebar, preview, settings):
        super().__init__(Qt.Orientation.Horizontal)
        self.setChildrenCollapsible(True)
        self.setHandleWidth(4)
        self.addWidget(sidebar)
        self.addWidget(preview)
        self.addWidget(settings)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)
        self.setStretchFactor(2, 0)
        self.setSizes([220, 700, 320])
