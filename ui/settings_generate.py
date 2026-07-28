from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox,QPushButton,QVBoxLayout
class SettingsGenerate(QGroupBox):
    generate_requested=Signal()
    def __init__(self):
        super().__init__("Generate")
        layout=QVBoxLayout(self); layout.setContentsMargins(8,12,8,8)
        self.button=QPushButton("Generate Audiobook"); self.button.setObjectName("generateButton"); self.button.setMinimumHeight(50)
        self.button.clicked.connect(self.generate_requested.emit); layout.addWidget(self.button); self.set_enabled(False)
    def set_enabled(self,enabled): self.button.setEnabled(bool(enabled))
    def set_text(self,text): self.button.setText(str(text))
    def enable(self): self.set_enabled(True)
    def disable(self): self.set_enabled(False)
