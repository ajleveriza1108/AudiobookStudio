from PySide6.QtCore import QObject


class ActionManager(QObject):

    def __init__(

        self,

        window

    ):

        super().__init__()

        self.window = window

    def connect(self):

        self.window.settings.book_selected.connect(

            self.window.import_book

        )

        self.window.settings.output_selected.connect(

            self.window.output_changed

        )

        self.window.settings.generate_requested.connect(

            self.window.generate

        )

        self.window.sidebar.book_selected.connect(

            self.window.book_selected

        )

        self.window.pause_button.clicked.connect(

            self.window.pause_generation

        )

        self.window.resume_button.clicked.connect(

            self.window.resume_generation

        )

        self.window.stop_button.clicked.connect(

            self.window.stop_generation

        )