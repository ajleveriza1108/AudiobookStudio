from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
)


class PreviewMetadata(QFrame):

    def __init__(self):

        super().__init__()

        self.setStyleSheet("""

QFrame{

background:#101010;

border:1px solid #2A2A2A;

border-radius:16px;

}

""")

        layout = QGridLayout(self)

        # ==========================================
        # FIX: Padding and Column Stretching
        # ==========================================
        layout.setContentsMargins(

            20,

            20,

            20,

            20

        )

        layout.setHorizontalSpacing(

            18

        )

        layout.setVerticalSpacing(

            10

        )
        
        layout.setColumnStretch(

            1,

            1

        )

        fields = [

            "Author",

            "Pages",

            "Language",

            "Type",

            "Duration",

            "Words",

            "Characters",

            "Chapters",

            "Engine",

            "Backend",

            "Estimated Size",

            "Output",

        ]

        self.values = {}

        for row, field in enumerate(fields):

            title = QLabel(field)

            title.setStyleSheet("""

font-weight:bold;

color:#BBBBBB;

""")

            value = QLabel("-")

            value.setWordWrap(True)

            layout.addWidget(

                title,

                row,

                0

            )

            layout.addWidget(

                value,

                row,

                1

            )

            self.values[field] = value

    def set_value(

        self,

        field,

        value,

    ):

        if field in self.values:

            self.values[field].setText(

                str(value)

            )

    def value(

        self,

        field,

    ):

        return self.values[field]

    def clear_values(self):

        for label in self.values.values():

            label.setText("-")