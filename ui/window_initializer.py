from PySide6.QtCore import Qt

from ui.ui_builder import UIBuilder
from ui.menu_bar import MainMenu
from ui.window_controller import WindowController


class WindowInitializer:

    def __init__(self, window):

        self.window = window

    def initialize(self):

        #
        # Window
        #

        self.window.setWindowTitle(
            "Audiobook Studio"
        )

        self.window.setMinimumSize(
            1600,
            900,
        )

        self.window.setFocusPolicy(
            Qt.StrongFocus
        )

        #
        # Build UI
        #

        UIBuilder(
            self.window
        ).build()

        #
        # Menu
        #

        MainMenu(
            self.window
        )

        #
        # Controller
        #

        self.window.controller = WindowController(
            self.window
        )

        #
        # Geometry
        #

        self.window.resize(
            1600,
            900,
        )

        self.window.showMaximized()

        return self.window