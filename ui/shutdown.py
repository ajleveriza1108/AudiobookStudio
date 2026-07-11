from ui.lifecycle import WindowLifecycle


class Shutdown:

    def __init__(self, window):

        self.window = window

    def run(self):

        WindowLifecycle(

            self.window

        ).save()

        if hasattr(

            self.window.controller,

            "threads"

        ):

            if self.window.controller.threads.running():

                self.window.controller.threads.stop()