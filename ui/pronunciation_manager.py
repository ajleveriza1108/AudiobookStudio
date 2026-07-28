from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.pronunciation import PronunciationDictionary


class PronunciationManagerDialog(QDialog):
    rules_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary = PronunciationDictionary()
        self.current_id: str | None = None
        self.setWindowTitle("Pronunciation Manager")
        self.resize(980, 620)
        self.build()
        self.refresh()

    def build(self):
        root = QVBoxLayout(self)
        intro = QLabel(
            "Control how names, abbreviations, numbers, and unusual terms are spoken. "
            "Rules are stored locally in pronunciation.json."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        splitter = QSplitter(Qt.Horizontal)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["On", "Written", "Spoken", "Matching"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._selected)
        splitter.addWidget(self.table)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        form = QFormLayout()
        self.source = QLineEdit()
        self.target = QLineEdit()
        self.whole_word = QCheckBox("Match complete words only")
        self.whole_word.setChecked(True)
        self.case_sensitive = QCheckBox("Case-sensitive")
        self.regex = QCheckBox("Regular expression (advanced)")
        self.enabled = QCheckBox("Enabled")
        self.enabled.setChecked(True)
        self.language = QComboBox()
        for label, code in (
            ("All languages", "all"),
            ("English", "en"),
            ("Tagalog / Filipino", "tl"),
            ("Spanish", "es"),
            ("French", "fr"),
            ("German", "de"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
        ):
            self.language.addItem(label, code)
        self.notes = QLineEdit()
        form.addRow("Written form", self.source)
        form.addRow("Spoken form", self.target)
        form.addRow("Language", self.language)
        form.addRow("Notes", self.notes)
        form.addRow("", self.whole_word)
        form.addRow("", self.case_sensitive)
        form.addRow("", self.regex)
        form.addRow("", self.enabled)
        editor_layout.addLayout(form)

        buttons = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.save_button = QPushButton("Save Rule")
        self.remove_button = QPushButton("Remove")
        buttons.addWidget(self.new_button)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.remove_button)
        editor_layout.addLayout(buttons)

        editor_layout.addWidget(QLabel("Test the selected rule"))
        self.test_input = QPlainTextEdit()
        self.test_input.setPlaceholderText("Type a sentence containing the written form.")
        self.test_output = QPlainTextEdit()
        self.test_output.setReadOnly(True)
        self.test_button = QPushButton("Apply Preview")
        editor_layout.addWidget(self.test_input, 1)
        editor_layout.addWidget(self.test_button)
        editor_layout.addWidget(self.test_output, 1)
        splitter.addWidget(editor)
        splitter.setSizes([500, 460])
        root.addWidget(splitter, 1)

        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(self.reject)
        root.addWidget(close)

        self.new_button.clicked.connect(self.clear_editor)
        self.save_button.clicked.connect(self.save_rule)
        self.remove_button.clicked.connect(self.remove_rule)
        self.test_button.clicked.connect(self.preview_rule)

    def refresh(self):
        rules = self.dictionary.list_rules()
        self.table.setRowCount(0)
        for row, rule in enumerate(rules):
            self.table.insertRow(row)
            enabled = QTableWidgetItem("Yes" if rule.get("enabled", True) else "No")
            enabled.setData(Qt.UserRole, str(rule.get("id", "")))
            source = QTableWidgetItem(str(rule.get("source", "")))
            target = QTableWidgetItem(str(rule.get("target", "")))
            matching = []
            if rule.get("regex"):
                matching.append("Regex")
            elif rule.get("whole_word"):
                matching.append("Whole word")
            else:
                matching.append("Anywhere")
            matching.append("Case" if rule.get("case_sensitive") else "Ignore case")
            self.table.setItem(row, 0, enabled)
            self.table.setItem(row, 1, source)
            self.table.setItem(row, 2, target)
            self.table.setItem(row, 3, QTableWidgetItem(", ".join(matching)))
        self.table.resizeColumnsToContents()

    def _selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        rule_id = str(self.table.item(row, 0).data(Qt.UserRole) or "")
        rule = next((item for item in self.dictionary.list_rules() if str(item.get("id")) == rule_id), None)
        if not rule:
            return
        self.current_id = rule_id
        self.source.setText(str(rule.get("source", "")))
        self.target.setText(str(rule.get("target", "")))
        self.whole_word.setChecked(bool(rule.get("whole_word", True)))
        self.case_sensitive.setChecked(bool(rule.get("case_sensitive", False)))
        self.regex.setChecked(bool(rule.get("regex", False)))
        self.enabled.setChecked(bool(rule.get("enabled", True)))
        language = str(rule.get("language", "all"))
        index = self.language.findData(language)
        self.language.setCurrentIndex(index if index >= 0 else 0)
        self.notes.setText(str(rule.get("notes", "")))

    def clear_editor(self):
        self.current_id = None
        self.source.clear()
        self.target.clear()
        self.whole_word.setChecked(True)
        self.case_sensitive.setChecked(False)
        self.regex.setChecked(False)
        self.enabled.setChecked(True)
        self.language.setCurrentIndex(0)
        self.notes.clear()
        self.table.clearSelection()
        self.source.setFocus()

    def _values(self) -> dict:
        source = self.source.text().strip()
        if not source:
            raise ValueError("Enter the written form that should be matched.")
        if self.regex.isChecked():
            re.compile(source)
        return {
            "source": source,
            "target": self.target.text(),
            "whole_word": self.whole_word.isChecked(),
            "case_sensitive": self.case_sensitive.isChecked(),
            "regex": self.regex.isChecked(),
            "enabled": self.enabled.isChecked(),
            "language": str(self.language.currentData() or "all"),
            "notes": self.notes.text().strip(),
        }

    def save_rule(self):
        try:
            values = self._values()
            if self.current_id:
                self.dictionary.update(self.current_id, **values)
            else:
                self.current_id = self.dictionary.add(**values)
            self.refresh()
            self.rules_changed.emit()
        except (ValueError, re.error) as error:
            QMessageBox.warning(self, "Pronunciation Rule", str(error))

    def remove_rule(self):
        if not self.current_id:
            return
        reply = QMessageBox.question(
            self,
            "Remove Rule",
            "Remove the selected pronunciation rule?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.dictionary.remove(self.current_id)
            self.clear_editor()
            self.refresh()
            self.rules_changed.emit()

    def preview_rule(self):
        try:
            values = self._values()
            self.test_output.setPlainText(
                self.dictionary.preview(self.test_input.toPlainText(), values)
            )
        except (ValueError, re.error) as error:
            QMessageBox.warning(self, "Pronunciation Preview", str(error))
