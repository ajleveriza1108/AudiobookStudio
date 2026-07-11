from ui.about_dialog import show_about


class MainWindowEvents:

    def __init__(self, window):

        self.window = window

    def connect(self):

        c = self.window.central

        f = self.window.footer

        g = self.window.controller.generation

        #
        # Settings
        #

        c.settings.book_selected.connect(

            self.window.controller.books.import_book

        )

        c.settings.output_selected.connect(

            self.window.output_changed

        )

        c.settings.generate_requested.connect(

            g.generate

        )

        #
        # Sidebar
        #

        c.sidebar.book_selected.connect(

            self.window.controller.books.selected

        )

        #
        # Footer
        #

        f.pause.clicked.connect(

            g.pause

        )

        f.resume.clicked.connect(

            g.resume

        )

        f.stop.clicked.connect(

            g.stop

        )

    def about(self):

        show_about(

            self.window

        )