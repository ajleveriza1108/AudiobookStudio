from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


# Configure CUDA before any package has a chance to import torch.
os.environ.setdefault("CUDA_MODULE_LOADING", "LAZY")
os.environ.setdefault(
    "PYTORCH_CUDA_ALLOC_CONF",
    "max_split_size_mb:128,expandable_segments:True",
)

from core.paths import PATHS  # noqa: E402

PATHS.ensure_runtime_directories()
os.chdir(PATHS.project_root)

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from core.cache import CacheManager  # noqa: E402
from core.config import Config  # noqa: E402
from core.library import Library  # noqa: E402
from core.logger import Logger  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


class AudiobookStudio:
    def __init__(self) -> None:
        self.config = Config()
        self.library = Library()
        self.cache = CacheManager(str(PATHS.cache))
        self.logger = Logger(str(PATHS.logs))

        try:
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception:
            pass

        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("Audiobook Studio")
        self.app.setOrganizationName("Audiobook Studio")
        self.app.aboutToQuit.connect(self.save_session)

        self.window = MainWindow()
        self.restore_session()
        sys.excepthook = self.handle_unhandled_exception

    @property
    def settings(self):
        return self.window.central.settings

    @property
    def sidebar(self):
        return self.window.central.sidebar

    @property
    def preview(self):
        return self.window.central.preview

    @property
    def console(self):
        return self.window.central.console

    def _log_error(self, message: str) -> None:
        try:
            self.logger.error(message)
        except Exception:
            print(message, file=sys.stderr)

    def handle_unhandled_exception(
        self,
        exception_type,
        exception_value,
        exception_traceback,
    ) -> None:
        details = "".join(
            traceback.format_exception(
                exception_type,
                exception_value,
                exception_traceback,
            )
        )
        self._log_error(details)

        try:
            QMessageBox.critical(
                self.window,
                "Audiobook Studio Error",
                f"An unexpected error occurred:\n\n{exception_value}\n\n"
                f"Details were written to:\n{PATHS.logs / 'audiobook.log'}",
            )
        except Exception:
            print(details, file=sys.stderr)

    def restore_session(self) -> None:
        try:
            width = max(900, int(self.config.get("window_width", 1536)))
            height = max(650, int(self.config.get("window_height", 864)))
            self.window.resize(width, height)

            if self.config.get("remember_last_book", True):
                for book in self.config.recent_books():
                    if Path(book).is_file():
                        try:
                            self.sidebar.add_book(book)
                        except Exception:
                            pass

                last_book = str(self.config.get("last_book", "") or "")
                if last_book and Path(last_book).is_file():
                    try:
                        self.sidebar.add_book(last_book)
                        self.preview.load_book(last_book)
                    except Exception:
                        pass

            try:
                self.settings.voice.setCurrentText(
                    str(self.config.get("voice", "af_heart"))
                )
                self.settings.speed.setValue(
                    float(self.config.get("speed", 1.0))
                )
                self.settings.pitch.setValue(
                    float(self.config.get("pitch", 0.0))
                )
            except Exception as error:
                self._log_error(f"Could not restore generation settings: {error}")

        except Exception as error:
            self._log_error(f"Could not restore session: {error}")

    def save_session(self) -> None:
        try:
            current_book = self.sidebar.current_book()
        except Exception:
            current_book = ""

        values = {
            "window_width": self.window.width(),
            "window_height": self.window.height(),
            "window_maximized": self.window.isMaximized(),
        }

        try:
            values.update(
                {
                    "voice": self.settings.current_voice(),
                    "speed": self.settings.current_speed(),
                    "pitch": self.settings.current_pitch(),
                }
            )
        except Exception as error:
            self._log_error(f"Could not read generation settings: {error}")

        if current_book:
            values["last_book"] = str(current_book)

        try:
            self.config.update(values)
        except Exception as error:
            self._log_error(f"Could not save session: {error}")

    def run(self) -> int:
        if self.config.get("window_maximized", False):
            self.window.showMaximized()
        else:
            self.window.show()

        return int(self.app.exec())


def main() -> int:
    studio = AudiobookStudio()
    return studio.run()


if __name__ == "__main__":
    raise SystemExit(main())
