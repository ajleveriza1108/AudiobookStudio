from ui.book_manager import BookManager
from ui.progress_manager import ProgressManager
from ui.thread_manager import ThreadManager
from ui.logger import ConsoleLogger

from controllers.generation_controller import GenerationController


class WindowController:

    def __init__(self, window):

        self.window = window

        self.books = BookManager(window)

        self.progress = ProgressManager()

        self.threads = ThreadManager(window)

        #
        # Logger
        #

        console_widget = None

        if hasattr(window.central, "console"):
            console_widget = window.central.console

        elif hasattr(window.central, "workspace"):

            if hasattr(window.central.workspace, "console"):
                console_widget = window.central.workspace.console

        elif hasattr(window, "workspace"):

            if hasattr(window.workspace, "console"):
                console_widget = window.workspace.console

        if console_widget is not None:

            self.logger = ConsoleLogger(
                console_widget
            )

        else:

            self.logger = None

        #
        # Generation Controller
        #

        self.generation = GenerationController(
            window
        )

    def log(self, message):

        if self.logger is not None:

            self.logger.write(message)