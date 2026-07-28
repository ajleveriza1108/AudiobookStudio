from __future__ import annotations

from controllers.generation_controller import GenerationController
from ui.book_manager import BookManager
from ui.logger import ConsoleLogger
from ui.progress_manager import ProgressManager
from ui.thread_manager import ThreadManager


class WindowController:
    def __init__(self, window):
        self.window = window
        self.books = BookManager(window)
        self.progress = ProgressManager()
        self.threads = ThreadManager(window)
        self.logger = ConsoleLogger(window.workspace.console)
        self.generation = GenerationController(window)

    def log(self, message):
        self.logger.write(message)
