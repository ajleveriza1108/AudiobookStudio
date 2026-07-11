from datetime import datetime

from PySide6.QtCore import Qt, Signal

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
    QAbstractItemView,
)


class JobMonitor(QWidget):

    clear_requested = Signal()

    def __init__(self):

        super().__init__()

        self.jobs = {}

        self.build_ui()

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)

        layout.setSpacing(10)

        title = QLabel("Generation Monitor")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
font-size:22px;
font-weight:bold;
""")

        layout.addWidget(title)

        self.table = QTableWidget()

        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels(

            [

                "Book",

                "Status",

                "Progress",

                "Started",

                "Finished",

                "Elapsed",

            ]

        )

        self.table.horizontalHeader().setSectionResizeMode(

            QHeaderView.Stretch

        )

        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(

            QAbstractItemView.SelectionBehavior.SelectRows

        )

        self.table.setSelectionMode(

            QAbstractItemView.SelectionMode.SingleSelection

        )

        self.table.setEditTriggers(

            QAbstractItemView.EditTrigger.NoEditTriggers

        )

        layout.addWidget(

            self.table,

            1

        )

        row = QHBoxLayout()

        layout.addLayout(row)

        self.clear_button = QPushButton(

            "Clear Finished"

        )

        row.addStretch()

        row.addWidget(

            self.clear_button

        )

        self.summary = QLabel()

        self.summary.setAlignment(

            Qt.AlignCenter

        )

        layout.addWidget(

            self.summary

        )

        self.clear_button.clicked.connect(

            self.clear_finished

        )

        self.update_summary()

    def update_summary(self):

        total = len(self.jobs)

        running = sum(

            1

            for job in self.jobs.values()

            if job["status"] == "Running"

        )

        finished = sum(

            1

            for job in self.jobs.values()

            if job["status"] == "Finished"

        )

        self.summary.setText(

            f"{total} Jobs   |   Running {running}   |   Finished {finished}"

        )

    def add_job(self, book):

        if book in self.jobs:

            return

        self.jobs[book] = {

            "status": "Waiting",

            "progress": 0,

            "started": datetime.now(),

            "finished": None,

        }

        row = self.table.rowCount()

        self.table.insertRow(row)

        self.table.setItem(

            row,

            0,

            QTableWidgetItem(book),

        )

        for col in range(1, 6):

            self.table.setItem(

                row,

                col,

                QTableWidgetItem(""),

            )

        self.update_job(

            book,

            "Waiting",

            0,

        )

    def update_job(

        self,

        book,

        status,

        progress,

    ):

        if book not in self.jobs:

            self.add_job(book)

        job = self.jobs[book]

        job["status"] = status

        job["progress"] = progress

        if status == "Finished":

            job["finished"] = datetime.now()

        for row in range(self.table.rowCount()):

            item = self.table.item(row, 0)

            if item is None:

                continue

            if item.text() != book:

                continue

            self.table.item(

                row,

                1,

            ).setText(status)

            self.table.item(

                row,

                2,

            ).setText(f"{progress}%")

            self.table.item(

                row,

                3,

            ).setText(

                job["started"].strftime(

                    "%H:%M:%S"

                )

            )

            if job["finished"] is not None:

                self.table.item(

                    row,

                    4,

                ).setText(

                    job["finished"].strftime(

                        "%H:%M:%S"

                    )

                )

                elapsed = int(

                    (

                        job["finished"]

                        -

                        job["started"]

                    ).total_seconds()

                )

                self.table.item(

                    row,

                    5,

                ).setText(

                    f"{elapsed} s"

                )

            break

        self.update_summary()

    def clear_finished(self):

        rows = []

        for row in range(

            self.table.rowCount()

        ):

            item = self.table.item(

                row,

                1,

            )

            if item and item.text() == "Finished":

                rows.append(row)

        for row in reversed(rows):

            title = self.table.item(

                row,

                0,

            ).text()

            self.jobs.pop(

                title,

                None,

            )

            self.table.removeRow(row)

        self.update_summary()

        self.clear_requested.emit()