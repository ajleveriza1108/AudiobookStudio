from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ChapterEditor(QWidget):
    plan_changed = Signal()

    def __init__(self):
        super().__init__()
        self._original: list[dict] = []
        self.build()

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        heading = QLabel("Chapter Review")
        heading.setStyleSheet("font-size:18px;font-weight:700;")
        help_text = QLabel(
            "Rename, reorder, or exclude detected chapters before generation. "
            "The original book file is never changed."
        )
        help_text.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(help_text)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Include", "Chapter title", "Words", "Est. time"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemChanged.connect(lambda *_: self.plan_changed.emit())
        layout.addWidget(self.table, 1)

        actions = QGridLayout()
        actions.setHorizontalSpacing(6)
        actions.setVerticalSpacing(4)
        self.up = QPushButton("Move Up")
        self.down = QPushButton("Move Down")
        self.include_all = QPushButton("Include All")
        self.exclude_all = QPushButton("Exclude All")
        self.reset = QPushButton("Reset")
        self.reset.setToolTip("Restore the automatically detected chapter order")
        actions.addWidget(self.up, 0, 0)
        actions.addWidget(self.down, 0, 1)
        actions.addWidget(self.reset, 0, 2)
        actions.addWidget(self.include_all, 1, 0)
        actions.addWidget(self.exclude_all, 1, 1)
        actions.setColumnStretch(2, 1)
        layout.addLayout(actions)

        self.up.clicked.connect(lambda: self._move(-1))
        self.down.clicked.connect(lambda: self._move(1))
        self.include_all.clicked.connect(lambda: self._set_all(True))
        self.exclude_all.clicked.connect(lambda: self._set_all(False))
        self.reset.clicked.connect(self.reset_plan)

    @staticmethod
    def _duration(words: int) -> str:
        minutes = words / 155 if words else 0
        if minutes < 1:
            return "< 1 min"
        if minutes < 60:
            return f"{round(minutes)} min"
        hours = int(minutes // 60)
        remaining = int(minutes % 60)
        return f"{hours}h {remaining}m"

    def load(self, chapters):
        self._original = deepcopy(list(chapters or []))
        self._populate(self._original)

    def _populate(self, chapters):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for row, chapter in enumerate(chapters):
            self.table.insertRow(row)
            include = QTableWidgetItem()
            include.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            include.setCheckState(Qt.Checked if chapter.get("included", True) else Qt.Unchecked)
            include.setData(Qt.UserRole, int(chapter.get("index", row)))

            title = QTableWidgetItem(str(chapter.get("title", f"Chapter {row + 1}")))
            title.setFlags(title.flags() | Qt.ItemIsEditable)
            words = int(chapter.get("word_count", 0))
            words_item = QTableWidgetItem(f"{words:,}")
            words_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            duration = QTableWidgetItem(self._duration(words))
            duration.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

            self.table.setItem(row, 0, include)
            self.table.setItem(row, 1, title)
            self.table.setItem(row, 2, words_item)
            self.table.setItem(row, 3, duration)
        self.table.blockSignals(False)
        if self.table.rowCount():
            self.table.selectRow(0)
        self.plan_changed.emit()

    def plan(self) -> list[dict]:
        plan: list[dict] = []
        for row in range(self.table.rowCount()):
            include = self.table.item(row, 0)
            title = self.table.item(row, 1)
            plan.append(
                {
                    "index": int(include.data(Qt.UserRole)),
                    "order": row,
                    "included": include.checkState() == Qt.Checked,
                    "title": title.text().strip() or f"Chapter {row + 1}",
                }
            )
        return plan

    def included_count(self) -> int:
        return sum(1 for item in self.plan() if item.get("included"))

    def _set_all(self, included: bool):
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(Qt.Checked if included else Qt.Unchecked)
        self.table.blockSignals(False)
        self.plan_changed.emit()

    def _move(self, direction: int):
        current = self.table.currentRow()
        target = current + direction
        if current < 0 or target < 0 or target >= self.table.rowCount():
            return
        plan = self.plan()
        plan[current], plan[target] = plan[target], plan[current]

        original_by_index = {int(item.get("index", index)): item for index, item in enumerate(self._original)}
        rebuilt = []
        for item in plan:
            base = dict(original_by_index.get(int(item["index"]), {}))
            base.update(item)
            rebuilt.append(base)
        self._populate(rebuilt)
        self.table.selectRow(target)

    def reset_plan(self):
        self._populate(deepcopy(self._original))

    def clear(self):
        self._original = []
        self.table.setRowCount(0)
