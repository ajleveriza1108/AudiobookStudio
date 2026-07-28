from __future__ import annotations


class ThemeManager:
    OLED = "dark"
    DIRTY_WHITE = "light"

    DISPLAY_NAMES = {OLED: "OLED Black", DIRTY_WHITE: "Dirty White"}

    @classmethod
    def normalize(cls, theme: str | None) -> str:
        value = str(theme or "dark").strip().lower()
        aliases = {
            "oled": cls.OLED,
            "oled black": cls.OLED,
            "black": cls.OLED,
            "dark": cls.OLED,
            "dirty white": cls.DIRTY_WHITE,
            "white": cls.DIRTY_WHITE,
            "light": cls.DIRTY_WHITE,
        }
        return aliases.get(value, cls.OLED)

    @classmethod
    def display_name(cls, theme: str | None) -> str:
        return cls.DISPLAY_NAMES[cls.normalize(theme)]

    @classmethod
    def apply(cls, application, theme: str | None) -> str:
        normalized = cls.normalize(theme)
        application.setStyleSheet(cls.dirty_white() if normalized == cls.DIRTY_WHITE else cls.oled())
        return normalized

    @staticmethod
    def oled():
        return """
QMainWindow, QWidget { background:#000000; color:#F2F2F2; font-family:"Segoe UI"; font-size:9pt; }
QFrame, QGroupBox { background:#090909; border:1px solid #242424; border-radius:7px; }
QLabel#coverPanel, QFrame#metadataPanel, QTextEdit#bookPreview { background:#0D0D0D; border:1px solid #292929; border-radius:7px; }
QLabel#metadataLabel, QLabel#helpText, QLabel#appSubtitle { color:#A3A3A3; }
QLabel#panelTitle, QLabel#dialogTitle, QLabel#appTitle { color:#FFFFFF; }
QLabel#statusBadge { background:#166534; color:#FFFFFF; border-radius:7px; padding:5px 9px; font-weight:700; }
QLabel { background:transparent; border:none; }
QGroupBox { margin-top:9px; padding-top:7px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:8px; padding:1px 5px; color:#E5E7EB; }
QPushButton, QToolButton { background:#171717; border:1px solid #303030; border-radius:6px; padding:4px 7px; min-height:25px; }
QPushButton:hover, QToolButton:hover { background:#242424; border-color:#4B5563; }
QPushButton:pressed, QToolButton:pressed { background:#303030; }
QPushButton:disabled, QToolButton:disabled { color:#666666; background:#0D0D0D; border-color:#202020; }
QToolButton:checked { background:#1D4ED8; color:#FFFFFF; border-color:#2563EB; }
QPushButton#generateButton:enabled, QPushButton#primaryButton:enabled { background:#16A34A; color:#FFFFFF; border:none; font-weight:700; }
QPushButton#generateButton:enabled:hover, QPushButton#primaryButton:enabled:hover { background:#15803D; }
QPushButton#generateButton:disabled { background:#242424; color:#777777; border:1px solid #363636; font-weight:700; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background:#111111; border:1px solid #303030; border-radius:6px; padding:4px 6px; min-height:24px; selection-background-color:#2563EB; }
QLineEdit[readOnly="true"] { color:#D1D5DB; background:#0D0D0D; }
QComboBox QAbstractItemView { background:#111111; color:#F2F2F2; selection-background-color:#2563EB; }
QListWidget, QTableWidget { background:#0D0D0D; border:1px solid #292929; border-radius:6px; outline:none; }
QListWidget::item { min-height:24px; padding:3px 5px; }
QListWidget::item:selected { background:#1D4ED8; }
QHeaderView::section { background:#171717; border:none; padding:5px; }
QProgressBar { border:1px solid #303030; border-radius:5px; background:#101010; text-align:center; min-height:17px; max-height:19px; }
QProgressBar::chunk { background:#2563EB; border-radius:4px; }
QTabWidget::pane { border:1px solid #252525; border-radius:6px; top:-1px; }
QTabBar::tab { background:#111111; border:1px solid #292929; padding:5px 8px; min-height:24px; }
QTabBar::tab:selected { background:#232323; color:#FFFFFF; }
QMenuBar, QStatusBar { background:#090909; }
QMenuBar::item { padding:4px 8px; }
QMenuBar::item:selected, QMenu::item:selected { background:#1D4ED8; }
QMenu { background:#111111; border:1px solid #2B2B2B; }
QMenu::item { padding:5px 22px; }
QCheckBox { spacing:6px; }
QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { width:9px; background:#0D0D0D; }
QScrollBar::handle:vertical { background:#444444; border-radius:4px; min-height:22px; }
QScrollBar:horizontal { height:9px; background:#0D0D0D; }
QScrollBar::handle:horizontal { background:#444444; border-radius:4px; min-width:22px; }
QScrollBar::add-line, QScrollBar::sub-line { width:0px; height:0px; }
QSplitter::handle { background:#1A1A1A; }
QToolTip { background:#1A1A1A; color:#FFFFFF; border:1px solid #4B5563; padding:4px; }
"""

    @staticmethod
    def dirty_white():
        return """
QMainWindow, QWidget { background:#F1EFE8; color:#1F2937; font-family:"Segoe UI"; font-size:9pt; }
QFrame, QGroupBox { background:#FAF9F5; border:1px solid #D5D1C7; border-radius:7px; }
QLabel#coverPanel, QFrame#metadataPanel, QTextEdit#bookPreview { background:#FFFFFF; border:1px solid #D2CEC4; border-radius:7px; }
QLabel#metadataLabel, QLabel#helpText, QLabel#appSubtitle { color:#6B7280; }
QLabel#panelTitle, QLabel#dialogTitle, QLabel#appTitle { color:#111827; }
QLabel#statusBadge { background:#15803D; color:#FFFFFF; border-radius:7px; padding:5px 9px; font-weight:700; }
QLabel { background:transparent; border:none; }
QGroupBox { margin-top:9px; padding-top:7px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:8px; padding:1px 5px; color:#374151; }
QPushButton, QToolButton { background:#FFFFFF; border:1px solid #C9C5BB; border-radius:6px; padding:4px 7px; min-height:25px; }
QPushButton:hover, QToolButton:hover { background:#E9E7DF; border-color:#9CA3AF; }
QPushButton:pressed, QToolButton:pressed { background:#DDDAD0; }
QPushButton:disabled, QToolButton:disabled { color:#9CA3AF; background:#EEECE6; border-color:#D8D5CD; }
QToolButton:checked { background:#BFDBFE; color:#1E3A8A; border-color:#93C5FD; }
QPushButton#generateButton:enabled, QPushButton#primaryButton:enabled { background:#15803D; color:#FFFFFF; border:none; font-weight:700; }
QPushButton#generateButton:enabled:hover, QPushButton#primaryButton:enabled:hover { background:#166534; }
QPushButton#generateButton:disabled { background:#E2DFD6; color:#9A968C; border:1px solid #CFCBC1; font-weight:700; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox { background:#FFFFFF; border:1px solid #C9C5BB; border-radius:6px; padding:4px 6px; min-height:24px; selection-background-color:#2563EB; }
QLineEdit[readOnly="true"] { color:#4B5563; background:#F5F3ED; }
QComboBox QAbstractItemView { background:#FFFFFF; color:#1F2937; selection-background-color:#BFDBFE; }
QListWidget, QTableWidget { background:#FFFFFF; border:1px solid #D2CEC4; border-radius:6px; outline:none; }
QListWidget::item { min-height:24px; padding:3px 5px; }
QListWidget::item:selected { background:#BFDBFE; color:#1E3A8A; }
QHeaderView::section { background:#E9E7DF; border:none; padding:5px; }
QProgressBar { border:1px solid #C9C5BB; border-radius:5px; background:#FFFFFF; text-align:center; min-height:17px; max-height:19px; }
QProgressBar::chunk { background:#2563EB; border-radius:4px; }
QTabWidget::pane { border:1px solid #D2CEC4; border-radius:6px; top:-1px; }
QTabBar::tab { background:#E9E7DF; border:1px solid #D2CEC4; padding:5px 8px; min-height:24px; }
QTabBar::tab:selected { background:#FFFFFF; color:#111827; }
QMenuBar, QStatusBar { background:#E7E4DC; }
QMenuBar::item { padding:4px 8px; }
QMenuBar::item:selected, QMenu::item:selected { background:#BFDBFE; }
QMenu { background:#FFFFFF; border:1px solid #C9C5BB; }
QMenu::item { padding:5px 22px; }
QCheckBox { spacing:6px; }
QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { width:9px; background:#ECE9E1; }
QScrollBar::handle:vertical { background:#AAA69C; border-radius:4px; min-height:22px; }
QScrollBar:horizontal { height:9px; background:#ECE9E1; }
QScrollBar::handle:horizontal { background:#AAA69C; border-radius:4px; min-width:22px; }
QScrollBar::add-line, QScrollBar::sub-line { width:0px; height:0px; }
QSplitter::handle { background:#D8D4CA; }
QToolTip { background:#FFFFFF; color:#111827; border:1px solid #9CA3AF; padding:4px; }
"""
