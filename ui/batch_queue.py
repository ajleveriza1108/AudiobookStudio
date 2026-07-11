from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QLabel,
    QMessageBox
)

from core.batch import BatchProcessor


class BatchQueue(QWidget):

    started = Signal()

    queue_changed = Signal(int)

    def __init__(self):

        super().__init__()

        self.batch = BatchProcessor()

        self.build_ui()

    def build_ui(self):

        layout = QVBoxLayout(self)

        title = QLabel("Batch Queue")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet(
            "font-size:22px;font-weight:bold;"
        )

        layout.addWidget(title)

        self.list = QListWidget()

        layout.addWidget(self.list, 1)

        buttons = QHBoxLayout()

        layout.addLayout(buttons)

        self.add_btn = QPushButton("Add")

        self.remove_btn = QPushButton("Remove")

        self.up_btn = QPushButton("▲")

        self.down_btn = QPushButton("▼")

        self.clear_btn = QPushButton("Clear")

        buttons.addWidget(self.add_btn)

        buttons.addWidget(self.remove_btn)

        buttons.addWidget(self.up_btn)

        buttons.addWidget(self.down_btn)

        buttons.addWidget(self.clear_btn)

        self.start_btn = QPushButton("Start Queue")

        self.start_btn.setMinimumHeight(45)

        layout.addWidget(self.start_btn)

        self.info = QLabel("0 Jobs")

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

        for job in self.batch.jobs():

            self.list.addItem(

                QListWidgetItem(

                    Path(job["source"]).name

                )

            )

        self.info.setText(

            f"{self.batch.pending()} Jobs"

        )

        self.queue_changed.emit(

            self.batch.pending()

        )

    def add_books(self):

        files, _ = QFileDialog.getOpenFileNames(

            self,

            "Select Books",

            "",

            "Books (*.pdf *.epub)"

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

                engine="kokoro"

            )

        self.refresh()

    def remove_job(self):

        row = self.list.currentRow()

        if row < 0:

            return

        self.batch.remove(row)

        self.refresh()

    def move_up(self):

        row = self.list.currentRow()

        if row < 1:

            return

        self.batch.move_up(row)

        self.refresh()

        self.list.setCurrentRow(row - 1)

    def move_down(self):

        row = self.list.currentRow()

        if row < 0:

            return

        self.batch.move_down(row)

        self.refresh()

        self.list.setCurrentRow(row + 1)

    def clear_jobs(self):

        reply = QMessageBox.question(

            self,

            "Clear Queue",

            "Remove all queued books?",

            QMessageBox.Yes |

            QMessageBox.No

        )

        if reply != QMessageBox.Yes:

            return

        self.batch.clear()

        self.refresh()

    def next_job(self):

        return self.batch.next()

    def empty(self):

        return self.batch.empty()