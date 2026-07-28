from __future__ import annotations

import traceback
from pathlib import Path

from core.logger import Logger
from core.paths import PATHS


class BookManager:
    def __init__(self, window):
        self.window = window
        self.book: Path | None = None

    def _open(self, filename, *, add_to_library: bool) -> bool:
        path = Path(filename).expanduser().resolve()
        if not path.is_file():
            self.window.show_error(
                "Book could not be opened",
                "The selected file no longer exists.",
            )
            return False

        try:
            self.window.central.sidebar.current_selected_path = str(path)
            self.window.central.preview.load_book(path)
            self.window.central.settings.set_book(path)
            # Add only after the book has reached a usable preview state. The
            # operation is idempotent, so startup restore and sidebar selection
            # also repair a missing/stale library entry automatically.
            self.window.central.sidebar.add_book(path)
        except Exception as error:
            # Keep the previously active book instead of leaving the GUI in a
            # half-selected state. Detailed support information stays in Logs.
            self.window.log(f"Book import failed: {path.name}: {error}")
            try:
                Logger(PATHS.logs).error(traceback.format_exc())
            except Exception:
                pass
            self.window.show_error(
                "Book could not be prepared",
                "Audiobook Studio could not finish preparing this book. "
                "The source file was not changed. See Activity and Logs for details.\n\n"
                f"Reason: {error}",
            )
            return False

        self.book = path
        self.window.config.append_recent_book(path)
        if add_to_library:
            self.window.log(f"Imported: {path.name}")
        self.window.header.set_status("Ready", state="ready")
        self.window.status_bar.set_message(f"Book ready: {path.name}")
        self.window.footer.set_left(path.name)

        cover_error = self.window.central.preview.cover.last_error()
        if cover_error:
            self.window.log(
                "Cover preview was skipped, but the book text remains available: "
                f"{cover_error}"
            )
        return True

    def import_book(self, filename):
        self._open(filename, add_to_library=True)

    def selected(self, filename):
        self._open(filename, add_to_library=True)

    def cleared(self):
        self.book = None
        self.window.central.preview.clear()
        self.window.central.settings.clear_book()
        self.window.footer.set_left("No active book")
        self.window.set_status("Ready")
