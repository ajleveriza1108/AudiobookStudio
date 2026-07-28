from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog,QGroupBox,QPushButton,QVBoxLayout
from core.config import Config
from ui.compact_widgets import CompactPathField
class SettingsOutput(QGroupBox):
    output_selected=Signal(str)
    def __init__(self):
        super().__init__("Output")
        self.config=Config(); layout=QVBoxLayout(self); layout.setContentsMargins(8,12,8,8); layout.setSpacing(6)
        self.button=QPushButton("Choose Output Folder")
        self.label=CompactPathField(str(self.config.get("output_folder","Output")))
        layout.addWidget(self.button); layout.addWidget(self.label); self.button.clicked.connect(self.select_output)
    def select_output(self):
        folder=QFileDialog.getExistingDirectory(self,"Select Output Folder")
        if folder: self.set_output(folder); self.output_selected.emit(folder)
    def current_output(self): return self.label.toolTip() or self.label.text()
    def set_output(self,folder): self.label.setValue(str(folder))
