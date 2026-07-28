from pathlib import Path
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QGroupBox, QPushButton, QVBoxLayout
from ui.compact_widgets import CompactPathField

class SettingsBook(QGroupBox):
    book_selected = Signal(str)
    def __init__(self):
        super().__init__("Book")
        layout=QVBoxLayout(self); layout.setContentsMargins(8,12,8,8); layout.setSpacing(6)
        self.button=QPushButton("Import PDF / EPUB")
        self.label=CompactPathField("No book selected")
        layout.addWidget(self.button); layout.addWidget(self.label)
        self.button.clicked.connect(self.select_book)
    def select_book(self):
        file,_=QFileDialog.getOpenFileName(self,"Import Book","","Books (*.pdf *.epub)")
        if file: self.set_book(file); self.book_selected.emit(file)
    def current_book(self): return None if self.label.text()=="No book selected" else self.label.toolTip()
    def set_book(self,file):
        if file:
            self.label.setValue(Path(file).name); self.label.setToolTip(str(file))
        else: self.label.setValue("No book selected")
