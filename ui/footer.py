from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Footer(QWidget):
    def __init__(self):
        super().__init__()
        self.build()

    def build(self):
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(3, 3, 3, 1)
        self.root.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(5)
        self.stage = QLabel("Idle")
        self.stage.setMinimumWidth(88)
        self.stage.setMaximumWidth(170)
        self.stage.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.percent = QLabel("0%")
        self.percent.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.percent.setFixedWidth(38)
        self.pause = QPushButton("Pause")
        self.resume = QPushButton("Resume")
        self.stop = QPushButton("Stop")
        for button in (self.pause, self.resume, self.stop):
            button.setMinimumWidth(54)
            button.setMaximumWidth(74)
            button.setEnabled(False)
        self.pause.setToolTip("Pause after the current narration operation")
        self.resume.setToolTip("Continue the paused audiobook")
        self.stop.setToolTip("Stop safely and keep completed sections")

        row.addWidget(self.stage)
        row.addWidget(self.progress, 1)
        row.addWidget(self.percent)
        row.addWidget(self.pause)
        row.addWidget(self.resume)
        row.addWidget(self.stop)

        self.info_widget = QWidget()
        self.info_row = QHBoxLayout(self.info_widget)
        self.info_row.setContentsMargins(0, 0, 0, 0)
        self.info_row.setSpacing(8)
        self.left = QLabel("No active book")
        self.center = QLabel("")
        self.right = QLabel("Checking engine…")
        self.left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.right.setObjectName("backendLabel")
        self.info_row.addWidget(self.left, 2)
        self.info_row.addWidget(self.center, 1)
        self.info_row.addWidget(self.right, 2)

        self.root.addLayout(row)
        self.root.addWidget(self.info_widget)
        self.setMinimumHeight(54)
        self.setMaximumHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_compact(self, compact):
        self.info_widget.setVisible(not compact)
        self.setMinimumHeight(36 if compact else 54)
        self.setMaximumHeight(44 if compact else 66)
        self.stage.setMaximumWidth(108 if compact else 170)
        if compact:
            self.pause.setText("Ⅱ")
            self.resume.setText("▶")
            self.stop.setText("■")
            for button in (self.pause, self.resume, self.stop):
                button.setFixedWidth(38)
        else:
            self.pause.setText("Pause")
            self.resume.setText("Resume")
            self.stop.setText("Stop")
            for button in (self.pause, self.resume, self.stop):
                button.setMinimumWidth(54)
                button.setMaximumWidth(74)

    def set_progress(self, value):
        safe = max(0, min(100, int(value)))
        self.progress.setValue(safe)
        self.percent.setText(f"{safe}%")

    def set_running(self, running):
        self.pause.setEnabled(running)
        self.resume.setEnabled(False)
        self.stop.setEnabled(running)

    def set_paused(self, paused):
        self.pause.setEnabled(not paused)
        self.resume.setEnabled(paused)
        self.stop.setEnabled(True)

    def set_left(self, text):
        self.left.setText(str(text))
        self.left.setToolTip(str(text))

    def set_center(self, text):
        self.center.setText(str(text))
        self.center.setToolTip(str(text))

    def set_right(self, text):
        self.right.setText(str(text))
        self.right.setToolTip(str(text))
