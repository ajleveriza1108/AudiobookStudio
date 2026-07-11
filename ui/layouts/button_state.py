from PySide6.QtCore import QObject


class ButtonState(QObject):

    def __init__(

        self,

        generate,

    ):

        super().__init__()

        self.generate = generate

        self.book_selected = False

        self.output_selected = True

    def set_book(

        self,

        value,

    ):

        self.book_selected = value

        self.update()

    def set_output(

        self,

        value,

    ):

        self.output_selected = value

        self.update()

    def update(self):

        enabled = (

            self.book_selected

            and

            self.output_selected

        )

        self.generate.set_enabled(

            enabled

        )