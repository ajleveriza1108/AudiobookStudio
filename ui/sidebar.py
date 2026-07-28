from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.library import Library


class Sidebar(QWidget):
    book_selected = Signal(str)
    book_cleared = Signal()

    def __init__(self):
        super().__init__()
        self.library = Library()
        self.filtered = []
        self.current_selected_path = None
        self.build_ui()
        self.refresh()

    def build_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(6)

        self.title = QLabel("Library")
        self.title.setObjectName("panelTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:17px;font-weight:700;padding:3px;")
        self.layout.addWidget(self.title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search books")
        self.search.setClearButtonEnabled(True)
        self.layout.addWidget(self.search)

        self.list = QListWidget()
        self.list.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.layout.addWidget(self.list, 1)

        controls = QGridLayout()
        controls.setHorizontalSpacing(5)
        controls.setVerticalSpacing(5)
        self.refresh_button = QPushButton("Refresh")
        self.favorite_button = QPushButton("Favorite")
        self.remove_button = QPushButton("Remove")
        self.refresh_button.setToolTip("Reload the library")
        self.favorite_button.setToolTip("Mark or unmark the selected book as a favorite")
        self.remove_button.setToolTip("Remove the selected book from Library; the file is not deleted")
        controls.addWidget(self.refresh_button, 0, 0)
        controls.addWidget(self.favorite_button, 0, 1)
        controls.addWidget(self.remove_button, 1, 0, 1, 2)
        self.layout.addLayout(controls)

        self.stats = QLabel()
        self.stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.stats)

        self.search.textChanged.connect(self.filter)
        self.refresh_button.clicked.connect(self.refresh)
        self.remove_button.clicked.connect(self.remove_selected)
        self.favorite_button.clicked.connect(self.favorite_selected)
        self.list.itemClicked.connect(self.open_item)
        self.list.itemDoubleClicked.connect(self.open_item)

    def set_compact(self, compact: bool) -> None:
        margins = 5 if compact else 8
        self.layout.setContentsMargins(margins, margins, margins, margins)
        self.title.setText("Books" if compact else "Library")
        self.favorite_button.setText("★" if compact else "Favorite")
        self.refresh_button.setText("↻" if compact else "Refresh")
        self.remove_button.setText("Remove")

    def refresh(self):
        self.filtered = self.library.all()
        self.populate()

    def populate(self):
        selected = self.current_selected_path
        self.list.clear()
        for book in self.filtered:
            prefix = "★ " if book["favorite"] else ""
            suffix = "  ✓" if book["completed"] else ""
            item = QListWidgetItem(prefix + book["title"] + suffix)
            item.setToolTip(book["path"])
            item.setData(Qt.ItemDataRole.UserRole, book["path"])
            self.list.addItem(item)
            if selected and str(book["path"]) == str(selected):
                self.list.setCurrentItem(item)
        count = len(self.filtered)
        self.stats.setText(f"{count} book{'s' if count != 1 else ''}")

    def filter(self, text):
        value = str(text).lower().strip()
        if not value:
            self.filtered = self.library.all()
        else:
            self.filtered = [
                item for item in self.library.all()
                if value in str(item.get("title", "")).lower()
                or value in Path(str(item.get("path", ""))).name.lower()
            ]
        self.populate()

    def add_book(self, file):
        self.library.add(file)
        self.current_selected_path = str(Path(file).expanduser().resolve())
        self.refresh()

    def open_item(self, item):
        path = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if not path:
            return
        self.current_selected_path = path
        self.library.touch(path)
        self.book_selected.emit(path)

    def remove_selected(self):
        item = self.list.currentItem()
        if item is None:
            return
        path = str(item.data(Qt.ItemDataRole.UserRole) or "")
        reply = QMessageBox.question(
            self,
            "Remove From Library",
            "Remove the selected book from Library? The original file will not be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.library.remove(path)
        self.current_selected_path = None
        self.refresh()
        self.book_cleared.emit()

    def favorite_selected(self):
        item = self.list.currentItem()
        if item is None:
            return
        path = str(item.data(Qt.ItemDataRole.UserRole) or "")
        self.library.favorite(path)
        self.refresh()

    def current_book(self):
        return self.current_selected_path
