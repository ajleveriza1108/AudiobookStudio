from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
)


class Header(QWidget):

    def __init__(self):

        super().__init__()

        self.build()

    def build(self):

        layout = QHBoxLayout(self)

        layout.setContentsMargins(

            0,

            0,

            0,

            0,

        )

        layout.setSpacing(

            12,

        )

        self.title = QLabel(

            "Audiobook Studio",

        )

        self.title.setStyleSheet("""

font-size:24px;

font-weight:bold;

padding:4px;

""")

        self.status = QLabel(

            "Ready",

        )

        self.status.setAlignment(

            Qt.AlignRight

        )

        self.status.setStyleSheet("""

padding:8px;

border-radius:10px;

background:#16A34A;

color:white;

font-weight:bold;

""")

        layout.addWidget(

            self.title,

        )

        layout.addStretch(

            1,

        )

        layout.addWidget(

            self.status,

        )

        self.setMinimumHeight(

            58,

        )

        self.setMaximumHeight(

            58,

        )

        self.setSizePolicy(

            QSizePolicy.Expanding,

            QSizePolicy.Fixed,

        )

    def set_status(

        self,

        text,

    ):

        self.status.setText(

            text,

        )