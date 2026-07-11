from PySide6.QtWidgets import (
    QWidget,
    QSizePolicy,
)


class ResponsiveLayout:

    SIDEBAR_WIDTH = 300
    SETTINGS_WIDTH = 380

    @staticmethod
    def apply(sidebar, preview, settings):

        sidebar.setMinimumWidth(
            ResponsiveLayout.SIDEBAR_WIDTH
        )

        sidebar.setMaximumWidth(
            ResponsiveLayout.SIDEBAR_WIDTH
        )

        sidebar.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )

        preview.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        settings.setMinimumWidth(
            ResponsiveLayout.SETTINGS_WIDTH
        )

        settings.setMaximumWidth(
            ResponsiveLayout.SETTINGS_WIDTH
        )

        settings.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Expanding,
        )