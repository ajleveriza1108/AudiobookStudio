class WindowLifecycle:

    def __init__(self, window):

        self.window = window

    def restore(self):

        config = self.window.config

        self.window.resize(

            config.get(

                "window_width",

                1800

            ),

            config.get(

                "window_height",

                950

            )

        )

    def save(self):

        config = self.window.config

        config.set(

            "window_width",

            self.window.width()

        )

        config.set(

            "window_height",

            self.window.height()

        )

        config.set(

            "voice",

            self.window.central.settings.current_voice()

        )

        config.set(

            "speed",

            self.window.central.settings.current_speed()

        )

        config.set(

            "pitch",

            self.window.central.settings.current_pitch()

        )