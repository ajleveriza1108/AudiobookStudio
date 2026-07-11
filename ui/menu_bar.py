from PySide6.QtGui import QAction


class MainMenu:

    def __init__(self, window):

        self.window = window

        self.build()

    def build(self):

        menubar = self.window.menuBar()

        file_menu = menubar.addMenu("File")
        tools_menu = menubar.addMenu("Tools")
        help_menu = menubar.addMenu("Help")

        self.import_book = QAction(
            "Import Book",
            self.window
        )

        self.output_folder = QAction(
            "Output Folder",
            self.window
        )

        self.exit = QAction(
            "Exit",
            self.window
        )

        self.clear_console = QAction(
            "Clear Console",
            self.window
        )

        self.self_test = QAction(
            "Run Self Test",
            self.window
        )

        self.about = QAction(
            "About",
            self.window
        )

        file_menu.addAction(self.import_book)
        file_menu.addAction(self.output_folder)
        file_menu.addSeparator()
        file_menu.addAction(self.exit)

        tools_menu.addAction(self.clear_console)
        tools_menu.addAction(self.self_test)

        help_menu.addAction(self.about)

        #
        # Import Book
        #

        if hasattr(self.window.central.settings, "book"):

            if hasattr(self.window.central.settings.book, "select_book"):

                self.import_book.triggered.connect(
                    self.window.central.settings.book.select_book
                )

            elif hasattr(self.window.central.settings.book, "browse"):

                self.import_book.triggered.connect(
                    self.window.central.settings.book.browse
                )

        #
        # Output Folder
        #

        if hasattr(self.window.central.settings, "output"):

            if hasattr(self.window.central.settings.output, "select_output"):

                self.output_folder.triggered.connect(
                    self.window.central.settings.output.select_output
                )

            elif hasattr(self.window.central.settings.output, "browse"):

                self.output_folder.triggered.connect(
                    self.window.central.settings.output.browse
                )

        #
        # Clear Console
        #

        if hasattr(self.window.central, "console"):

            if hasattr(self.window.central.console, "clear"):

                self.clear_console.triggered.connect(
                    self.window.central.console.clear
                )

        #
        # Self Test
        #

        if hasattr(self.window, "run_self_test"):

            self.self_test.triggered.connect(
                self.window.run_self_test
            )
        else:

            self.self_test.setEnabled(False)

        #
        # About
        #

        if hasattr(self.window, "about"):

            self.about.triggered.connect(
                self.window.about
            )
        else:

            self.about.setEnabled(False)

        #
        # Exit
        #

        self.exit.triggered.connect(
            self.window.close
        )