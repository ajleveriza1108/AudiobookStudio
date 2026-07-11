from PySide6.QtWidgets import (
    QLabel,
    QStatusBar,
)


class MainStatusBar(QStatusBar):

    def __init__(self):

        super().__init__()

        self.message = QLabel("Ready")

        self.eta = QLabel("ETA --:--")

        self.backend = QLabel()

        self.addWidget(

            self.message,

            1

        )

        self.addPermanentWidget(

            self.backend

        )

        self.addPermanentWidget(

            self.eta

        )

    def set_backend(

        self,

        backend

    ):

        self.backend.setText(

            backend

        )

    def set_eta(

        self,

        eta

    ):

        self.eta.setText(

            eta

        )

    def set_message(

        self,

        message

    ):

        self.message.setText(

            message

        )