from __future__ import annotations


class MainWindowEvents:
    def __init__(self, window):
        self.window = window

    def connect(self):
        central = self.window.central
        footer = self.window.footer
        generation = self.window.controller.generation

        central.settings.book_selected.connect(self.window.controller.books.import_book)
        central.settings.output_selected.connect(self.window.output_changed)
        central.settings.generate_requested.connect(generation.generate)
        central.settings.settings_changed.connect(self.window.save_generation_settings)
        central.settings.engine_status_changed.connect(self.window.engine_status_changed)

        central.sidebar.book_selected.connect(self.window.controller.books.selected)
        central.sidebar.book_removed.connect(self.window.controller.books.removed)
        central.sidebar.book_cleared.connect(self.window.controller.books.cleared)

        footer.pause.clicked.connect(generation.pause)
        footer.resume.clicked.connect(generation.resume)
        footer.stop.clicked.connect(generation.stop)

        self.window.workspace.queue.started.connect(generation.generate_queue)
        self.window.header.theme_changed.connect(self.window.theme_changed)
        self.window.header.library_toggled.connect(self.window.responsive.set_library_visible)
        self.window.header.settings_toggled.connect(self.window.responsive.set_settings_visible)
        self.window.header.activity_toggled.connect(self.window.responsive.set_activity_visible)
