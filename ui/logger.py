class ConsoleLogger:

    def __init__(

        self,

        console

    ):

        self.console = console

    def write(

        self,

        message

    ):

        self.console.append(

            str(message)

        )

        bar = self.console.verticalScrollBar()

        bar.setValue(

            bar.maximum()

        )

    def log(

        self,

        message

    ):

        self.write(

            message

        )

    __call__ = write