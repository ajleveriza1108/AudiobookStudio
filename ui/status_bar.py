from __future__ import annotations

from PySide6.QtWidgets import QLabel, QStatusBar


class MainStatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.message = QLabel("Ready")
        self.eta = QLabel("ETA --:--")
        self.backend = QLabel("Checking narration engine…")
        self.addWidget(self.message, 1)
        self.addPermanentWidget(self.backend)
        self.addPermanentWidget(self.eta)

    def set_backend(self, backend):
        self.backend.setText(str(backend))

    def set_eta(self, eta):
        self.eta.setText(str(eta))

    def set_message(self, message):
        self.message.setText(str(message))
