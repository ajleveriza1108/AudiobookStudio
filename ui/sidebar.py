from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QMessageBox,
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("📚 Library")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
            padding:8px;
        """)
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        layout.addWidget(self.search)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        row = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.favorite_button = QPushButton("★")
        self.remove_button = QPushButton("Remove")

        row.addWidget(self.refresh_button)
        row.addWidget(self.favorite_button)
        row.addWidget(self.remove_button)

        layout.addLayout(row)

        self.stats = QLabel()
        self.stats.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats)

        # =========================
        # SIGNALS
        # =========================
        self.search.textChanged.connect(self.filter)
        self.refresh_button.clicked.connect(self.refresh)
        self.remove_button.clicked.connect(self.remove_selected)
        self.favorite_button.clicked.connect(self.favorite_selected)

        self.list.itemClicked.connect(self.open_item)
        self.list.itemDoubleClicked.connect(self.open_item)

    def refresh(self):

        self.filtered = self.library.all()
        self.populate()

    def populate(self):

        self.list.clear()

        for book in self.filtered:

            icon = "⭐ " if book["favorite"] else "📖 "
            title = icon + book["title"]

            if book["completed"]:
                title += " ✓"

            item = QListWidgetItem(title)
            item.setToolTip(book["path"])

            self.list.addItem(item)

        self.stats.setText(f"{len(self.filtered)} Books")

    def filter(self, text):

        text = text.lower().strip()

        if not text:
            self.refresh()
            return

        self.filtered = [
            x for x in self.library.all()
            if text in x["title"].lower()
        ]

        self.populate()

    def add_book(self, file):

        self.library.add(file)
        self.refresh()

    def open_item(self, item):

        row = self.list.row(item)

        if row < 0:
            return

        book = self.filtered[row]

        self.current_selected_path = book["path"]

        self.library.touch(book["path"])

        self.book_selected.emit(book["path"])

    def remove_selected(self):

        row = self.list.currentRow()

        if row < 0:
            return

        reply = QMessageBox.question(
            self,
            "Remove",
            "Remove selected book?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.library.remove(self.filtered[row]["path"])
        self.refresh()

        self.current_selected_path = None
        self.book_cleared.emit()

    def favorite_selected(self):

        row = self.list.currentRow()

        if row < 0:
            return

        self.library.favorite(self.filtered[row]["path"])
        self.refresh()

    def current_book(self):

        return self.current_selected_path