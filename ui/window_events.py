from ui.dragdrop import DragDropHandler
from ui.shutdown import Shutdown


class WindowEvents:

    def __init__(self, window):

        self.window = window

        self.dragdrop = DragDropHandler(

            window

        )

    def drag_enter(

        self,

        event

    ):

        self.dragdrop.drag_enter(

            event

        )

    def drop(

        self,

        event

    ):

        self.dragdrop.drop(

            event

        )

    def close(

        self,

        event

    ):

        Shutdown(

            self.window

        ).run()

        event.accept()