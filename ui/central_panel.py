from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.layouts import MainLayout, ResponsiveLayout
from ui.preview import PreviewPanel
from ui.settings import SettingsPanel
from ui.sidebar import Sidebar


class CentralPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.console = None
        self.workspace = None
        self.build()

    def build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.preview = PreviewPanel()
        self.settings = SettingsPanel()

        ResponsiveLayout.apply(self.sidebar, self.preview, self.settings)
        self.main_layout = MainLayout(self.sidebar, self.preview, self.settings)
        root.addWidget(self.main_layout, 1)

    def clear_console(self):
        if self.console is not None:
            self.console.clear()

    def log(self, text):
        if self.console is not None:
            self.console.append(str(text))
