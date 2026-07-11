from pathlib import Path


class BookManager:

    def __init__(self, window):

        self.window = window

        self.book = None

    def import_book(

        self,

        filename

    ):

        self.book = Path(filename)

        self.window.central.sidebar.add_book(

            filename

        )

        self.window.central.preview.load_book(

            filename

        )

        self.window.config.append_recent_book(

            filename

        )

        self.window.central.console.append(

            f"Imported: {self.book.name}"

        )

        self.window.status_bar.set_message(

            self.book.name

        )

    def selected(

        self,

        filename

    ):

        self.book = Path(filename)

        self.window.central.preview.load_book(

            filename

        )

        self.window.status_bar.set_message(

            self.book.name

        )