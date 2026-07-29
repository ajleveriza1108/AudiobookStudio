from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QProcess, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.advanced_ocr import AdvancedOCRCompatibility, REPORT_FILE
from core.config import Config
from core.optional_engines import advanced_ocr_runtime_ready
from core.paths import PATHS


class SettingsAdvancedOCR(QGroupBox):
    settings_changed = Signal()
    status_changed = Signal(str)

    def __init__(self):
        super().__init__("Advanced Layout OCR")
        self.config = Config()
        self._report = AdvancedOCRCompatibility.load_report()
        self._busy = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        self.enabled = QCheckBox("Use Unlimited-OCR for difficult scanned pages")
        self.enabled.setToolTip(
            "Checks this laptop first. RapidOCR remains available as a safe fallback."
        )
        self.help = QLabel(
            "Optional local parser for timelines, columns, tables, and complex page layouts. "
            "It requires a compatible NVIDIA laptop and a separate large model download."
        )
        self.help.setWordWrap(True)
        self.help.setObjectName("helpText")
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(self.status.textInteractionFlags())
        self.status.setObjectName("helpText")

        button_grid = QGridLayout()
        button_grid.setContentsMargins(0, 0, 0, 0)
        button_grid.setHorizontalSpacing(6)
        button_grid.setVerticalSpacing(6)
        self.check_button = QPushButton("Check Laptop")
        self.install_button = QPushButton("Install Module")
        self.report_button = QPushButton("Open Report")
        self.check_button.setMinimumWidth(0)
        self.install_button.setMinimumWidth(0)
        self.report_button.setMinimumWidth(0)
        button_grid.addWidget(self.check_button, 0, 0)
        button_grid.addWidget(self.install_button, 0, 1)
        button_grid.addWidget(self.report_button, 1, 0, 1, 2)

        layout.addWidget(self.enabled)
        layout.addWidget(self.help)
        layout.addWidget(self.status)
        layout.addLayout(button_grid)

        self.enabled.toggled.connect(self._toggle_requested)
        self.check_button.clicked.connect(lambda: self.check_laptop())
        self.install_button.clicked.connect(self.install_module)
        self.report_button.clicked.connect(self.open_report)
        self.refresh()

    def refresh(self) -> None:
        self._report = AdvancedOCRCompatibility.load_report()
        can_enable = bool(self._report and self._report.get("can_enable"))
        configured = bool(self.config.get("advanced_ocr_enabled", False))
        self.enabled.blockSignals(True)
        self.enabled.setChecked(configured and can_enable)
        self.enabled.blockSignals(False)
        self.install_button.setEnabled(can_enable and not advanced_ocr_runtime_ready())
        self.report_button.setEnabled(Path(REPORT_FILE).is_file())
        summary = AdvancedOCRCompatibility.display_summary(self._report)
        if configured and can_enable and advanced_ocr_runtime_ready():
            summary += " Advanced OCR is enabled and ready; RapidOCR remains the fallback."
        elif configured and can_enable:
            summary += " Install the optional module before it can process pages."
        self.status.setText(summary)
        self.status.setToolTip(summary)
        self.status_changed.emit(summary)

    def _set_checked(self, checked: bool) -> None:
        self.enabled.blockSignals(True)
        self.enabled.setChecked(bool(checked))
        self.enabled.blockSignals(False)

    def _toggle_requested(self, checked: bool) -> None:
        if self._busy:
            return
        if not checked:
            self.config.set("advanced_ocr_enabled", False)
            self.refresh()
            self.settings_changed.emit()
            return
        report = self.check_laptop(show_dialog=False)
        if not report or not report.get("can_enable"):
            self.config.set("advanced_ocr_enabled", False)
            self._set_checked(False)
            QMessageBox.warning(
                self,
                "Advanced OCR Not Available",
                AdvancedOCRCompatibility.display_summary(report),
            )
            self.refresh()
            return
        if str(report.get("status")) == "experimental":
            answer = QMessageBox.question(
                self,
                "Experimental Hardware",
                AdvancedOCRCompatibility.display_summary(report)
                + "\n\nEnable experimental mode anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.config.set("advanced_ocr_enabled", False)
                self._set_checked(False)
                self.refresh()
                return
        self.config.set("advanced_ocr_enabled", True)
        self.refresh()
        self.settings_changed.emit()

    def check_laptop(self, *, show_dialog: bool = True):
        if self._busy:
            return self._report
        self._busy = True
        self.check_button.setEnabled(False)
        self.status.setText("Checking Windows, CPU, RAM, storage, NVIDIA GPU, and VRAM…")
        try:
            report = AdvancedOCRCompatibility.check_and_record(config=self.config)
            self._report = report
        except Exception as error:
            self._report = None
            self.status.setText(f"Capability check could not complete: {error}")
            if show_dialog:
                QMessageBox.critical(self, "Capability Check Failed", str(error))
            return None
        finally:
            self._busy = False
            self.check_button.setEnabled(True)
        self.refresh()
        if show_dialog:
            title = "Advanced OCR Supported" if report.get("status") == "supported" else (
                "Advanced OCR Experimental" if report.get("can_enable") else "Advanced OCR Unsupported"
            )
            QMessageBox.information(
                self,
                title,
                AdvancedOCRCompatibility.display_summary(report),
            )
        return report

    def install_module(self) -> None:
        report = self._report or AdvancedOCRCompatibility.load_report()
        if not report or not report.get("can_enable"):
            report = self.check_laptop(show_dialog=False)
        if not report or not report.get("can_enable"):
            QMessageBox.warning(
                self,
                "Advanced OCR Not Available",
                AdvancedOCRCompatibility.display_summary(report),
            )
            return
        script = PATHS.project_root / "install_advanced_ocr.ps1"
        if not script.is_file():
            QMessageBox.critical(self, "Installer Missing", f"Missing installer: {script}")
            return
        arguments = [
            "-NoExit",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-ProjectRoot",
            str(PATHS.project_root),
        ]
        if str(report.get("status")) == "experimental":
            arguments.append("-AllowExperimental")
        started = QProcess.startDetached("powershell.exe", arguments)
        if not started:
            QMessageBox.critical(
                self,
                "Could Not Start Installer",
                "Open PowerShell in the Audiobook Studio folder and run install_advanced_ocr.ps1.",
            )

    def open_report(self) -> None:
        path = Path(REPORT_FILE)
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def set_generation_running(self, running: bool) -> None:
        self.enabled.setEnabled(not running)
        self.check_button.setEnabled(not running and not self._busy)
        self.install_button.setEnabled(
            not running
            and bool(self._report and self._report.get("can_enable"))
            and not advanced_ocr_runtime_ready()
        )
        self.report_button.setEnabled(not running and Path(REPORT_FILE).is_file())
