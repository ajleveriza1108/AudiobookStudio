from pathlib import Path


class DragDropHandler:

    def __init__(self, window):

        self.window = window

    def drag_enter(self, event):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()

        else:

            event.ignore()

    def drop(self, event):

        for url in event.mimeData().urls():

            file = Path(

                url.toLocalFile()

            )

            if file.suffix.lower() in (

                ".pdf",

                ".epub"

            ):

                self.window.controller.books.import_book(

                    str(file)

                )

        event.acceptProposedAction()