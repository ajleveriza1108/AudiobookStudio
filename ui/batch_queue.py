from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.batch import BatchProcessor


class BatchQueue(QWidget):
    started = Signal()
    queue_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.batch = BatchProcessor()
        self.build_ui()
        self.refresh()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(7)

        title = QLabel("Batch Queue")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:17px;font-weight:700;")
        layout.addWidget(title)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(6)
        buttons.setVerticalSpacing(4)
        self.add_btn = QPushButton("Add Books")
        self.remove_btn = QPushButton("Remove")
        self.up_btn = QPushButton("Move Up")
        self.down_btn = QPushButton("Move Down")
        self.clear_btn = QPushButton("Clear")
        buttons.addWidget(self.add_btn, 0, 0)
        buttons.addWidget(self.remove_btn, 0, 1)
        buttons.addWidget(self.clear_btn, 0, 2)
        buttons.addWidget(self.up_btn, 1, 0)
        buttons.addWidget(self.down_btn, 1, 1)
        buttons.setColumnStretch(2, 1)
        layout.addLayout(buttons)

        self.start_btn = QPushButton("Start Queue")
        self.start_btn.setMinimumHeight(38)
        layout.addWidget(self.start_btn)

        self.info = QLabel("0 books waiting")
        self.info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info)

        self.add_btn.clicked.connect(self.add_books)
        self.remove_btn.clicked.connect(self.remove_job)
        self.up_btn.clicked.connect(self.move_up)
        self.down_btn.clicked.connect(self.move_down)
        self.clear_btn.clicked.connect(self.clear_jobs)
        self.start_btn.clicked.connect(self.started.emit)

    def refresh(self):
        self.list.clear()
        for job in self.batch.all():
            item = QListWidgetItem(Path(job.source).name)
            item.setToolTip(str(job.source))
            self.list.addItem(item)

        count = self.batch.pending()
        self.info.setText(f"{count} book{'s' if count != 1 else ''} waiting")
        self.start_btn.setEnabled(count > 0)
        self.queue_changed.emit(count)

    def add_books(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Books",
            "",
            "Books (*.pdf *.epub)",
        )
        if not files:
            return

        for file in files:
            self.batch.add(
                source=file,
                output="Output",
                voice="af_heart",
                speed=1.0,
                pitch=0,
                engine="kokoro",
            )
        self.refresh()

    def remove_job(self):
        row = self.list.currentRow()
        if row >= 0:
            self.batch.remove(row)
            self.refresh()

    def move_up(self):
        row = self.list.currentRow()
        if row < 1:
            return
        jobs = self.batch.jobs
        jobs[row - 1], jobs[row] = jobs[row], jobs[row - 1]
        self.refresh()
        self.list.setCurrentRow(row - 1)

    def move_down(self):
        row = self.list.currentRow()
        jobs = self.batch.jobs
        if row < 0 or row >= len(jobs) - 1:
            return
        jobs[row + 1], jobs[row] = jobs[row], jobs[row + 1]
        self.refresh()
        self.list.setCurrentRow(row + 1)

    def clear_jobs(self):
        if self.batch.empty():
            return
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Remove all queued books?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.batch.clear()
            self.refresh()

    def queued_sources(self) -> list[str]:
        return [str(job.source) for job in self.batch.all()]

    def clear_after_start(self):
        self.batch.clear()
        self.refresh()

    def next_job(self):
        return self.batch.next()

    def empty(self):
        return self.batch.empty()
