
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QSizePolicy,
)


class MainLayout(QHBoxLayout):

    def __init__(self, sidebar, preview, settings):

        super().__init__()

        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(10)

        sidebar.setMinimumWidth(300)
        sidebar.setMaximumWidth(300)
        sidebar.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        preview.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        settings.setMinimumWidth(380)
        settings.setMaximumWidth(380)
        settings.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        self.addWidget(sidebar)
        self.addWidget(preview, 1)
        self.addWidget(settings)