from PySide6.QtCore import QTimer

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)

import psutil


class SystemMonitor(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        self.cpu = QLabel()

        self.ram = QLabel()

        self.gpu = QLabel()

        self.vram = QLabel()

        layout.addWidget(self.cpu)

        layout.addWidget(self.ram)

        layout.addWidget(self.gpu)

        layout.addWidget(self.vram)

        layout.addStretch()

        self.timer = QTimer()

        self.timer.timeout.connect(

            self.refresh

        )

        self.timer.start(

            1000

        )

        self.refresh()

    def refresh(self):

        self.cpu.setText(

            f"CPU Usage : {psutil.cpu_percent()} %"

        )

        memory = psutil.virtual_memory()

        self.ram.setText(

            f"RAM Usage : {memory.percent} %"

        )

        try:

            from core.system_info import SystemInfo

            gpu = SystemInfo.gpu()

            if gpu.get(

                "available",

                False

            ):

                self.gpu.setText(

                    gpu["name"]

                )

                self.vram.setText(

                    "GPU Ready"

                )

            else:

                self.gpu.setText(

                    "CPU Mode"

                )

                self.vram.setText(

                    "VRAM : N/A"

                )

        except Exception:

            self.gpu.setText(

                "Unknown"

            )

            self.vram.setText(

                "VRAM : Unknown"

            )