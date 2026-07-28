from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget

from ui.theme_manager import ThemeManager


class Header(QWidget):
    theme_changed = Signal(str)
    library_toggled = Signal(bool)
    settings_toggled = Signal(bool)
    activity_toggled = Signal(bool)

    def __init__(self):
        super().__init__()
        self.build()

    @staticmethod
    def _panel_button(text: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setText(text)
        button.setCheckable(True)
        button.setChecked(True)
        button.setToolTip(tooltip)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setMinimumWidth(66)
        return button

    def build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(6)

        self.title = QLabel("Audiobook Studio")
        self.title.setObjectName("appTitle")
        self.title.setStyleSheet("font-size:19px;font-weight:700;padding:2px;")
        self.title.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.subtitle = QLabel("Book to audiobook workspace")
        self.subtitle.setObjectName("appSubtitle")
        self.subtitle.setStyleSheet("font-size:9pt;color:#808080;")

        self.library_button = self._panel_button("Library", "Show or hide the book library")
        self.settings_button = self._panel_button("Settings", "Show or hide production settings")
        self.activity_button = self._panel_button("Activity", "Show or hide activity, statistics, and queue")

        self.theme = QComboBox()
        self.theme.addItem("OLED", ThemeManager.OLED)
        self.theme.addItem("Light", ThemeManager.DIRTY_WHITE)
        self.theme.setToolTip("Change application appearance")
        self.theme.setMinimumWidth(82)
        self.theme.setMaximumWidth(100)

        self.status = QLabel("Ready")
        self.status.setObjectName("statusBadge")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setMinimumWidth(86)
        self.status.setMaximumWidth(160)
        self.status.setToolTip("Application status")

        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addStretch(1)
        layout.addWidget(self.library_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.activity_button)
        layout.addWidget(self.theme)
        layout.addWidget(self.status)

        self.theme.currentIndexChanged.connect(self._theme_selected)
        self.library_button.toggled.connect(self.library_toggled.emit)
        self.settings_button.toggled.connect(self.settings_toggled.emit)
        self.activity_button.toggled.connect(self.activity_toggled.emit)
        self.setMinimumHeight(40)
        self.setMaximumHeight(46)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_compact(self, compact: bool, very_compact: bool = False) -> None:
        self.subtitle.setVisible(not compact)
        self.title.setText("Audiobook Studio" if not very_compact else "Audiobook")
        for button in (self.library_button, self.settings_button, self.activity_button):
            button.setMinimumWidth(56 if compact else 66)
        self.status.setVisible(not very_compact)

    def set_panel_states(self, *, library: bool, settings: bool, activity: bool) -> None:
        for button, value in (
            (self.library_button, library),
            (self.settings_button, settings),
            (self.activity_button, activity),
        ):
            button.blockSignals(True)
            button.setChecked(bool(value))
            button.blockSignals(False)

    def _theme_selected(self):
        self.theme_changed.emit(str(self.theme.currentData() or ThemeManager.OLED))

    def set_theme(self, theme: str):
        normalized = ThemeManager.normalize(theme)
        index = self.theme.findData(normalized)
        if index >= 0:
            self.theme.blockSignals(True)
            self.theme.setCurrentIndex(index)
            self.theme.blockSignals(False)

    def current_theme(self) -> str:
        return str(self.theme.currentData() or ThemeManager.OLED)

    def set_status(self, text, state="ready"):
        del state
        value = str(text or "Ready")
        self.status.setText(value if len(value) <= 18 else value[:17] + "…")
        self.status.setToolTip(value)
