from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLineEdit, QSizePolicy


class CompactPathField(QLineEdit):
    """Compact read-only path/title field.

    QLineEdit already supports mouse/keyboard selection and copying while
    read-only.  Do not call QLabel-only text interaction APIs here.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(str(text), parent)
        self.setReadOnly(True)
        self.setFrame(False)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setCursorPosition(0)
        self.setToolTip(str(text or ""))

    def setValue(self, value: str) -> None:
        text = str(value or "")
        self.setText(text)
        self.setToolTip(text)
        self.setCursorPosition(0)


def compact_form(layout: QFormLayout) -> QFormLayout:
    layout.setContentsMargins(8, 12, 8, 8)
    layout.setHorizontalSpacing(8)
    layout.setVerticalSpacing(6)
    layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
    return layout
