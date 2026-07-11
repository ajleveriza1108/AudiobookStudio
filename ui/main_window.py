from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow

from ui.startup import Startup


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        #
        # High DPI / Screen Setup
        # Note: Qt.WA_DeleteOnClose was removed from here to prevent 
        # the app.py save_session() crash.
        #

        screen = QGuiApplication.primaryScreen()

        geometry = screen.availableGeometry()

        #
        # Window
        #

        self.setWindowTitle(

            "Audiobook Studio"

        )

        self.setMinimumSize(

            1600,

            900,

        )

        #
        # Build UI
        #

        Startup(

            self,

        ).run()

        #
        # Always maximize using the
        # same proportions as windowed.
        #

        self.resize(

            geometry.width(),

            geometry.height(),

        )

        self.showMaximized()

    def closeEvent(

        self,

        event,

    ):

        try:

            if hasattr(

                self,

                "controller",

            ):

                if hasattr(

                    self.controller,

                    "threads",

                ):

                    # Fixed: ThreadManager uses stop() and cleanup(), not shutdown()
                    if self.controller.threads.running():
                        self.controller.threads.stop()
                        
                    self.controller.threads.cleanup()

        except Exception as e:

            print(f"Error closing threads: {e}")

        event.accept()