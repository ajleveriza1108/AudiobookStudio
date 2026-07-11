from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QGridLayout
)


class LiveStatistics(QWidget):

    def __init__(self):

        super().__init__()

        layout = QGridLayout(self)

        self.percent = QLabel("0 %")

        self.chunk = QLabel("0 / 0")

        self.elapsed = QLabel("0 sec")

        self.characters = QLabel("0")

        self.words = QLabel("0")

        self.speed = QLabel("0 chars/sec")

        labels = [

            ("Progress", self.percent),

            ("Chunk", self.chunk),

            ("Elapsed", self.elapsed),

            ("Characters", self.characters),

            ("Words", self.words),

            ("Speed", self.speed)

        ]

        for row, (title, widget) in enumerate(labels):

            layout.addWidget(

                QLabel(title),

                row,

                0

            )

            layout.addWidget(

                widget,

                row,

                1

            )

    def update_statistics(

        self,

        stats

    ):

        self.percent.setText(

            f"{stats['percent']} %"

        )

        self.chunk.setText(

            f"{stats['generated']} / {stats['total']}"

        )

        self.elapsed.setText(

            f"{stats['elapsed']} sec"

        )

        self.characters.setText(

            f"{stats['characters']:,}"

        )

        self.words.setText(

            f"{stats['words']:,}"

        )

        self.speed.setText(

            f"{stats['characters_per_second']} chars/sec"

        )