from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from ui.sidebar import Sidebar
from ui.preview import PreviewPanel
from ui.settings import SettingsPanel

from ui.layouts import (
    MainLayout,
    ResponsiveLayout,
)


class CentralPanel(QWidget):

    def __init__(self):

        super().__init__()

        self.build()

    def build(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(

            0,

            0,

            0,

            0,

        )

        root.setSpacing(

            10

        )

        self.sidebar = Sidebar()
        
        # ==========================================
        # FIX: Prevent Sidebar from being crushed
        # ==========================================
        self.sidebar.setMinimumWidth(280)

        self.preview = PreviewPanel()
        
        # ==========================================
        # FIX: Prevent Preview from vanishing
        # ==========================================
        self.preview.setMinimumWidth(500)

        self.settings = SettingsPanel()
        
        # ==========================================
        # FIX: Stop Settings Checkboxes from cropping
        # ==========================================
        self.settings.setMinimumWidth(320)

        ResponsiveLayout.apply(

            self.sidebar,

            self.preview,

            self.settings,

        )

        self.main_layout = MainLayout(

            self.sidebar,

            self.preview,

            self.settings,

        )

        root.addLayout(

            self.main_layout,

            1,

        )

    def clear_console(self):

        pass

    def log(

        self,

        text,

    ):

        pass