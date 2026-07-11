from PySide6.QtWidgets import QMessageBox


class WorkerCallbacks:

    def __init__(self, window):

        self.window = window

    # =========================
    # PROGRESS BAR
    # =========================
    def progress(self, value):

        try:

            self.window.footer.progress.setValue(value)
            self.window.footer.percent.setText(f"{value}%")

        except Exception:
            pass

    # =========================
    # STATUS BAR
    # =========================
    def status(self, message):

        try:

            self.window.status_bar.set_message(message)

        except Exception:
            pass

    # =========================
    # LOG OUTPUT (FIXED)
    # =========================
    def log(self, message):

        try:

            # MAIN FIX: always write to central console
            self.window.central.console.append(message)

        except Exception:
            pass

    # =========================
    # STATISTICS
    # =========================
    def statistics(self, stats):

        try:

            if hasattr(self.window.central, "workspace"):

                if hasattr(self.window.central.workspace, "statistics"):

                    self.window.central.workspace.statistics.update_statistics(stats)

        except Exception:
            pass

    # =========================
    # CURRENT BOOK
    # =========================
    def current_book(self, book):

        try:

            self.window.status_bar.set_message(f"Processing: {book}")

        except Exception:
            pass

    # =========================
    # FINISHED
    # =========================
    def finished(self):

        try:

            self.window.controller.generation.finished()

            self.window.central.console.append("✔ Generation completed")

            self.window.footer.progress.setValue(100)
            self.window.footer.percent.setText("100%")

        except Exception:
            pass

    # =========================
    # CANCELLED
    # =========================
    def cancelled(self):

        try:

            self.window.controller.generation.cancelled()

            self.window.central.console.append("⛔ Generation cancelled")

        except Exception:
            pass

    # =========================
    # ERROR
    # =========================
    def error(self, message):

        try:

            self.window.controller.generation.cancelled()

            self.window.central.console.append(f"❌ Error: {message}")

            QMessageBox.critical(
                self.window,
                "Generation Failed",
                str(message)
            )

        except Exception:
            pass