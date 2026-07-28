from __future__ import annotations

from PySide6.QtWidgets import QSizePolicy


class ResponsiveLayout:
    @staticmethod
    def apply(sidebar, preview, settings):
        sidebar.setMinimumWidth(150)
        sidebar.setMaximumWidth(360)
        sidebar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        preview.setMinimumWidth(340)
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        settings.setMinimumWidth(260)
        settings.setMaximumWidth(430)
        settings.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
