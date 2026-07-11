from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QSizePolicy,
)


class Footer(QWidget):

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

            10,

        )

        self.left = QLabel(

            "Ready"

        )

        self.center = QLabel(

            ""

        )

        self.right = QLabel(

            "GPU"

        )

        self.left.setAlignment(

            Qt.AlignLeft

        )

        self.center.setAlignment(

            Qt.AlignCenter

        )

        self.right.setAlignment(

            Qt.AlignRight

        )

        self.left.setStyleSheet("""

padding:6px;

""")

        self.center.setStyleSheet("""

padding:6px;

""")

        self.right.setStyleSheet("""

padding:6px;

font-weight:bold;

color:#22C55E;

""")

        layout.addWidget(

            self.left,

            1,

        )

        layout.addWidget(

            self.center,

            1,

        )

        layout.addWidget(

            self.right,

            1,

        )

        self.setMinimumHeight(

            36,

        )

        self.setMaximumHeight(

            36,

        )

        self.setSizePolicy(

            QSizePolicy.Expanding,

            QSizePolicy.Fixed,

        )

    def set_left(

        self,

        text,

    ):

        self.left.setText(

            text,

        )

    def set_center(

        self,

        text,

    ):

        self.center.setText(

            text,

        )

    def set_right(

        self,

        text,

    ):

        self.right.setText(

            text,

        )