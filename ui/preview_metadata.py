from __future__ import annotations
from PySide6.QtWidgets import QFrame,QGridLayout,QLabel
class PreviewMetadata(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("metadataPanel")
        layout=QGridLayout(self); layout.setContentsMargins(10,9,10,9); layout.setHorizontalSpacing(10); layout.setVerticalSpacing(4); layout.setColumnStretch(1,1)
        fields=["Author","Pages","Language","Type","Duration","Words","Characters","Chapters","Preparation","Engine","Backend","Estimated Size","Output"]
        self.values={}
        for row,field in enumerate(fields):
            title=QLabel(field); title.setObjectName("metadataLabel"); title.setStyleSheet("font-weight:600;")
            value=QLabel("-"); value.setWordWrap(True); value.setToolTip("-")
            layout.addWidget(title,row,0); layout.addWidget(value,row,1); self.values[field]=value
    def set_value(self,field,value):
        if field in self.values: self.values[field].setText(str(value)); self.values[field].setToolTip(str(value))
    def value(self,field): return self.values[field]
    def clear_values(self):
        for label in self.values.values(): label.setText("-"); label.setToolTip("-")
