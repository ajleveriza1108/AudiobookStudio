from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget


def _format_time(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining = seconds % 60
    return f"{hours:02}:{minutes:02}:{remaining:02}"


class LiveStatistics(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(6)

        self.percent = QLabel("0%")
        self.chunk = QLabel("0 / 0")
        self.elapsed = QLabel("00:00:00")
        self.eta = QLabel("--:--:--")
        self.characters = QLabel("0")
        self.words = QLabel("0")
        self.speed = QLabel("0 chars/sec")

        labels = [
            ("Progress", self.percent),
            ("Section", self.chunk),
            ("Elapsed", self.elapsed),
            ("Estimated remaining", self.eta),
            ("Characters processed", self.characters),
            ("Words processed", self.words),
            ("Narration speed", self.speed),
        ]

        for row, (title, widget) in enumerate(labels):
            label = QLabel(title)
            label.setStyleSheet("font-weight:600;")
            layout.addWidget(label, row, 0)
            layout.addWidget(widget, row, 1)

        layout.setColumnStretch(1, 1)

    def reset(self):
        self.update_statistics(
            {
                "percent": 0,
                "generated": 0,
                "total": 0,
                "elapsed": 0,
                "eta_seconds": 0,
                "characters": 0,
                "words": 0,
                "characters_per_second": 0,
            }
        )

    def update_statistics(self, stats):
        self.percent.setText(f"{int(stats.get('percent', 0))}%")
        self.chunk.setText(
            f"{int(stats.get('generated', 0))} / {int(stats.get('total', 0))}"
        )
        self.elapsed.setText(_format_time(int(stats.get("elapsed", 0))))
        eta_seconds = int(stats.get("eta_seconds", 0))
        self.eta.setText(_format_time(eta_seconds) if eta_seconds else "--:--:--")
        self.characters.setText(f"{int(stats.get('characters', 0)):,}")
        self.words.setText(f"{int(stats.get('words', 0)):,}")
        self.speed.setText(
            f"{int(stats.get('characters_per_second', 0)):,} chars/sec"
        )
