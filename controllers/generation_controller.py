from pathlib import Path

from PySide6.QtWidgets import QMessageBox


class GenerationController:

    def __init__(self, window):

        self.window = window

    def generate(self):

        book = self.window.controller.books.book

        if not book:

            QMessageBox.warning(

                self.window,

                "No Book",

                "Please import a PDF or EPUB."

            )

            return

        options = self.window.central.settings.export_options()

        # =========================
        # UI STATE (START)
        # =========================
        self.window.controller.progress.begin()

        self.window.footer.pause.setEnabled(True)
        self.window.footer.resume.setEnabled(False)
        self.window.footer.stop.setEnabled(True)

        self.window.central.settings.generate.setEnabled(False)

        # =========================
        # THREAD START (FIXED CONTRACT)
        # =========================
        self.window.controller.threads.start(

            book=book,

            output=str(self.window.output_folder),

            voice=self.window.central.settings.current_voice(),

            speed=self.window.central.settings.current_speed(),

            pitch=self.window.central.settings.current_pitch(),

            export_options=options

        )

    def pause(self):

        self.window.controller.threads.pause()

        self.window.footer.pause.setEnabled(False)
        self.window.footer.resume.setEnabled(True)

    def resume(self):

        self.window.controller.threads.resume()

        self.window.footer.pause.setEnabled(True)
        self.window.footer.resume.setEnabled(False)

    def stop(self):

        self.window.controller.threads.stop()

    def finished(self):

        self.window.footer.pause.setEnabled(False)
        self.window.footer.resume.setEnabled(False)
        self.window.footer.stop.setEnabled(False)

        self.window.central.settings.generate.setEnabled(True)

        self.window.footer.progress.setValue(100)
        self.window.footer.percent.setText("100%")

    def cancelled(self):

        self.window.footer.pause.setEnabled(False)
        self.window.footer.resume.setEnabled(False)
        self.window.footer.stop.setEnabled(False)

        self.window.central.settings.generate.setEnabled(True)