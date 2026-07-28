from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from core.config import Config
from core.engine_service import EngineService
from core.paths import PATHS
from core.self_test import SelfTest
from ui.startup import Startup
from ui.theme_manager import ThemeManager


class MainWindow(QMainWindow):
    def __init__(self, config: Config | None = None):
        super().__init__()
        self.config = config or Config()
        self.output_folder = PATHS.resolve(self.config.get("output_folder", "Output"))
        Startup(self).run()
        self.central.settings.set_output(str(self.output_folder))
        self.header.set_theme(self.config.get("theme", "dark"))
        self.footer.set_left("No active book")
        self.refresh_engine_status()

    @property
    def settings(self):
        return self.central.settings

    @property
    def sidebar(self):
        return self.central.sidebar

    @property
    def preview(self):
        return self.central.preview

    @property
    def console(self):
        return self.workspace.console

    def log(self, message):
        self.workspace.log(str(message))

    def set_status(self, message, state="ready"):
        # Keep a single general status message. The footer's left side is
        # reserved for the active book, avoiding three duplicate "Ready" rows.
        self.status_bar.set_message(str(message))
        self.header.set_status(str(message), state=state)

    def show_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def refresh_engine_status(self, *_args) -> None:
        settings = self.central.settings
        if EngineService.loaded():
            engine_name = EngineService.current_name() or settings.current_engine()
            message = f"{engine_name.title()} loaded • {EngineService.backend()}"
            available = True
        else:
            available = settings.engine_available()
            message = settings.engine_status_text()

        self.footer.set_right(message)
        self.status_bar.set_backend(message)
        if self.preview.current_book:
            self.preview.meta.set_value("Backend", message)

        if not available:
            self.log(f"Narration engine unavailable: {message}")

    def engine_status_changed(self, available: bool, message: str) -> None:
        del available
        self.footer.set_right(message)
        self.status_bar.set_backend(message)
        if self.preview.current_book and not EngineService.loaded():
            self.preview.meta.set_value("Backend", message)

    def output_changed(self, folder):
        path = Path(folder).expanduser()
        if not path.is_absolute():
            path = PATHS.resolve(path)
        self.output_folder = path.resolve()
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.central.settings.set_output(str(self.output_folder))
        self.central.preview.meta.set_value("Output", str(self.output_folder))
        self.config.set("output_folder", str(self.output_folder))
        self.log(f"Output folder: {self.output_folder}")

    def save_generation_settings(self, *_):
        settings = self.central.settings
        options = settings.export_options()
        self.config.update(
            {
                "engine": settings.current_engine(),
                "voice": settings.current_voice(),
                "speed": settings.current_speed(),
                "pitch": settings.current_pitch(),
                "output_folder": str(self.output_folder),
                "export_wav": options.get("wav", True),
                "export_mp3": options.get("mp3", False),
                "export_m4b": options.get("m4b", False),
                "overwrite": options.get("overwrite", False),
                "delete_chunks": options.get("delete_chunks", False),
                "bitrate": options.get("bitrate", "192k"),
            }
        )

    def theme_changed(self, theme):
        application = QApplication.instance()
        normalized = ThemeManager.apply(application, theme) if application else ThemeManager.normalize(theme)
        self.header.set_theme(normalized)
        self.config.set("theme", normalized)

    def run_self_test(self):
        try:
            report = SelfTest.run()
            self.log("Self test completed.")
            if report:
                self.log(report)
            QMessageBox.information(
                self,
                "Self Test Complete",
                "The basic Audiobook Studio checks completed. See Activity for details.",
            )
        except Exception as error:
            self.log(f"Self test error: {error}")
            self.show_error("Self Test Could Not Complete", str(error))

    def about(self):
        from ui.about_dialog import show_about

        show_about(self)

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
        if any(Path(url.toLocalFile()).suffix.lower() in {".pdf", ".epub"} for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in {".pdf", ".epub"} and path.is_file():
                self.controller.books.import_book(path)
                event.acceptProposedAction()
                return
        event.ignore()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        responsive = getattr(self, "responsive", None)
        if responsive is not None:
            responsive.schedule()

    def closeEvent(self, event):
        if self.controller.threads.running():
            reply = QMessageBox.question(
                self,
                "Close Audiobook Studio",
                "Narration is still running. Stop safely and close the application?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.controller.threads.cleanup(wait_ms=30000)
            if self.controller.threads.running():
                QMessageBox.information(
                    self,
                    "Finishing Current Audio Section",
                    "Audiobook Studio is still finishing the current audio operation. "
                    "Please wait a little longer, then close again.",
                )
                event.ignore()
                return

        try:
            EngineService.unload()
        except Exception:
            pass
        event.accept()
