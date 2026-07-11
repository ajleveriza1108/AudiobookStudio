import os
import sys

# =========================================================
# CUDA / TORCH SAFE INITIALIZATION
# =========================================================

os.environ["CUDA_MODULE_LOADING"] = "LAZY"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

import torch

try:
    if torch.cuda.is_available():
        _ = torch.tensor([1], device="cuda")
except Exception:
    pass

# =========================================================
# QT IMPORT
# =========================================================

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow

from core.config import Config
from core.library import Library
from core.cache import CacheManager
from core.logger import Logger


class AudiobookStudio:

    def __init__(self):

        # =========================
        # CORE SYSTEMS
        # =========================

        self.config = Config()
        self.library = Library()
        self.cache = CacheManager("Cache")
        self.logger = Logger()

        # =========================
        # QT APP
        # =========================

        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Audiobook Studio")
        self.app.setOrganizationName("Audiobook Studio")

        # =========================
        # MAIN WINDOW
        # =========================

        self.window = MainWindow()

        self.restore_session()

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

    def restore_session(self):

        try:

            self.window.resize(
                self.config.get("window_width", 1850),
                self.config.get("window_height", 1000),
            )

            recent = self.config.recent_books()

            for book in recent:

                try:
                    self.sidebar.add_book(book)
                except Exception:
                    pass

            last = self.config.get("last_book", "")

            if last:

                try:
                    self.sidebar.add_book(last)
                    self.preview.load_book(last)
                except Exception:
                    pass

            self.settings.voice.setCurrentText(
                self.config.get("voice", "af_heart")
            )

            self.settings.speed.setValue(
                self.config.get("speed", 1.0)
            )

            self.settings.pitch.setValue(
                self.config.get("pitch", 0)
            )

        except Exception as e:

            try:
                self.logger.write(str(e))
            except Exception:
                print(e)

    def save_session(self):

        self.config.set(
            "window_width",
            self.window.width(),
        )

        self.config.set(
            "window_height",
            self.window.height(),
        )

        self.config.set(
            "voice",
            self.settings.current_voice(),
        )

        self.config.set(
            "speed",
            self.settings.current_speed(),
        )

        self.config.set(
            "pitch",
            self.settings.current_pitch(),
        )

        current = self.sidebar.current_book()

        if current:
            self.config.set(
                "last_book",
                current,
            )

    def run(self):

        self.window.show()

        code = self.app.exec()

        self.save_session()

        sys.exit(code)


def main():

    studio = AudiobookStudio()
    studio.run()


if __name__ == "__main__":
    main()