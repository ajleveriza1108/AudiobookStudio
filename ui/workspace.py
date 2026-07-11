from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTextEdit,
    QSizePolicy,
)

from ui.live_statistics import LiveStatistics
from ui.batch_queue import BatchQueue
from ui.logger import ConsoleLogger


class Workspace(QWidget):

    def __init__(self):

        super().__init__()

        self.build()

    def build(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.setSpacing(8)

        self.tabs = QTabWidget()

        #
        # LOGS
        #

        self.console = QTextEdit()

        self.console.setReadOnly(True)

        self.logger = ConsoleLogger(
            self.console
        )

        #
        # LIVE STATISTICS
        #

        self.statistics = LiveStatistics()

        #
        # BATCH QUEUE
        #

        self.queue = BatchQueue()

        self.tabs.addTab(
            self.console,
            "Logs",
        )

        self.tabs.addTab(
            self.statistics,
            "Statistics",
        )

        self.tabs.addTab(
            self.queue,
            "Queue",
        )

        self.tabs.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        root.addWidget(
            self.tabs
        )

        self.setMinimumHeight(220)

        self.setMaximumHeight(260)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

    def log(self, text):

        self.logger.write(text)

    def clear(self):

        self.console.clear()

    def update_statistics(
        self,
        stats,
    ):

        self.statistics.update_statistics(
            stats
        )