class WindowState:

    def __init__(

        self,

        window

    ):

        self.window = window

    def save(self):

        c = self.window.config

        c.set(

            "window_width",

            self.window.width()

        )

        c.set(

            "window_height",

            self.window.height()

        )

        c.set(

            "voice",

            self.window.settings.current_voice()

        )

        c.set(

            "speed",

            self.window.settings.current_speed()

        )

        c.set(

            "pitch",

            self.window.settings.current_pitch()

        )

    def restore(self):

        c = self.window.config

        self.window.resize(

            c.get(

                "window_width",

                1800

            ),

            c.get(

                "window_height",

                950

            )

        )