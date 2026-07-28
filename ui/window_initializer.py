from __future__ import annotations

from PySide6.QtCore import Qt

from ui.main_window_events import MainWindowEvents
from ui.menu_bar import MainMenu
from ui.status_bar import MainStatusBar
from ui.ui_builder import UIBuilder
from ui.window_controller import WindowController


class WindowInitializer:
    def __init__(self, window):
        self.window = window

    def initialize(self):
        self.window.setWindowTitle("Audiobook Studio")
        self.window.setMinimumSize(900, 620)
        self.window.setFocusPolicy(Qt.StrongFocus)
        self.window.setAcceptDrops(True)

        UIBuilder(self.window).build()
        self.window.status_bar = MainStatusBar()
        self.window.setStatusBar(self.window.status_bar)
        self.window.controller = WindowController(self.window)
        MainWindowEvents(self.window).connect()
        self.window.main_menu = MainMenu(self.window)
        return self.window
