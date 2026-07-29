from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence


class MainMenu:
    def __init__(self, window):
        self.window = window
        self.build()

    def build(self):
        menubar = self.window.menuBar()
        file_menu = menubar.addMenu("File")
        view_menu = menubar.addMenu("View")
        tools_menu = menubar.addMenu("Tools")
        help_menu = menubar.addMenu("Help")

        self.import_book = QAction("Import Book…", self.window)
        self.import_book.setShortcut(QKeySequence.StandardKey.Open)
        self.output_folder = QAction("Choose Output Folder…", self.window)
        self.open_output = QAction("Open Output Folder", self.window)
        self.exit = QAction("Exit", self.window)
        self.exit.setShortcut(QKeySequence.StandardKey.Quit)

        self.show_library = QAction("Library", self.window)
        self.show_library.setCheckable(True)
        self.show_library.setChecked(True)
        self.show_library.setShortcut(QKeySequence("Ctrl+L"))
        self.show_settings = QAction("Settings", self.window)
        self.show_settings.setCheckable(True)
        self.show_settings.setChecked(True)
        self.show_settings.setShortcut(QKeySequence("Ctrl+,"))
        self.show_activity = QAction("Activity", self.window)
        self.show_activity.setCheckable(True)
        self.show_activity.setChecked(True)
        self.show_activity.setShortcut(QKeySequence("Ctrl+J"))

        self.voice_preview = QAction("Voice Preview…", self.window)
        self.voice_studio = QAction("Voice Studio…", self.window)
        self.pronunciation = QAction("Pronunciation Manager…", self.window)
        self.advanced_ocr = QAction("Advanced OCR Compatibility…", self.window)
        self.clear_console = QAction("Clear Activity", self.window)
        self.self_test = QAction("Run Self Test", self.window)
        self.about = QAction("About", self.window)

        file_menu.addAction(self.import_book)
        file_menu.addAction(self.output_folder)
        file_menu.addAction(self.open_output)
        file_menu.addSeparator()
        file_menu.addAction(self.exit)

        view_menu.addAction(self.show_library)
        view_menu.addAction(self.show_settings)
        view_menu.addAction(self.show_activity)

        tools_menu.addAction(self.voice_preview)
        tools_menu.addAction(self.voice_studio)
        tools_menu.addAction(self.pronunciation)
        tools_menu.addAction(self.advanced_ocr)
        tools_menu.addSeparator()
        tools_menu.addAction(self.clear_console)
        tools_menu.addAction(self.self_test)
        help_menu.addAction(self.about)

        self.import_book.triggered.connect(self.window.central.settings.book.select_book)
        self.output_folder.triggered.connect(self.window.central.settings.output.select_output)
        self.open_output.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.window.output_folder)))
        )
        self.show_library.toggled.connect(self.window.header.library_button.setChecked)
        self.show_settings.toggled.connect(self.window.header.settings_button.setChecked)
        self.show_activity.toggled.connect(self.window.header.activity_button.setChecked)
        self.window.header.library_button.toggled.connect(self.show_library.setChecked)
        self.window.header.settings_button.toggled.connect(self.show_settings.setChecked)
        self.window.header.activity_button.toggled.connect(self.show_activity.setChecked)
        self.voice_preview.triggered.connect(self.window.central.settings.open_voice_preview)
        self.voice_studio.triggered.connect(self.window.central.settings.open_voice_studio)
        self.pronunciation.triggered.connect(self.window.central.settings.open_pronunciation_manager)
        self.advanced_ocr.triggered.connect(self.window.central.settings.open_advanced_ocr)
        self.clear_console.triggered.connect(self.window.workspace.clear)
        self.self_test.triggered.connect(self.window.run_self_test)
        self.about.triggered.connect(self.window.about)
        self.exit.triggered.connect(self.window.close)
