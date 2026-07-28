from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPlainTextEdit,QSizePolicy,QTabWidget,QVBoxLayout,QWidget
from ui.batch_queue import BatchQueue
from ui.live_statistics import LiveStatistics
from ui.logger import ConsoleLogger
class Workspace(QWidget):
    def __init__(self): super().__init__(); self.build()
    def build(self):
        root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.tabs=QTabWidget(); self.tabs.setDocumentMode(True); self.tabs.setUsesScrollButtons(True); self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.console=QPlainTextEdit(); self.console.setReadOnly(True); self.console.setMaximumBlockCount(10000); self.console.setPlaceholderText("Production messages appear here.")
        self.logger=ConsoleLogger(self.console); self.statistics=LiveStatistics(); self.queue=BatchQueue()
        self.tabs.addTab(self.console,"Activity"); self.tabs.addTab(self.statistics,"Statistics"); self.tabs.addTab(self.queue,"Queue")
        self.tabs.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding); root.addWidget(self.tabs); self.setMinimumHeight(110)
    def log(self,text): self.logger.write(text)
    def clear(self): self.console.clear()
    def update_statistics(self,stats): self.statistics.update_statistics(stats)
