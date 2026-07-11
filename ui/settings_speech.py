from PySide6.QtWidgets import (
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
)


class SettingsSpeech(QGroupBox):

    def __init__(self):

        super().__init__("Speech")

        layout = QFormLayout(self)
        
        layout.setContentsMargins(
            12, 
            16, 
            12, 
            12
        )
        
        layout.setSpacing(
            10
        )

        self.speed = QDoubleSpinBox()

        self.speed.setRange(

            0.50,

            2.00

        )

        self.speed.setSingleStep(

            0.05

        )

        self.speed.setValue(

            1.00

        )

        self.pitch = QSpinBox()

        self.pitch.setRange(

            -12,

            12

        )

        self.pitch.setValue(

            0

        )

        layout.addRow(

            "Speed",

            self.speed

        )

        layout.addRow(

            "Pitch",

            self.pitch

        )

    def current_speed(self):

        return self.speed.value()

    def current_pitch(self):

        return self.pitch.value()

    def set_speed(

        self,

        value

    ):

        self.speed.setValue(

            value

        )

    def set_pitch(

        self,

        value

    ):

        self.pitch.setValue(

            value

        )