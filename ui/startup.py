from core.startup import initialize

from ui.window_initializer import WindowInitializer


class Startup:

    def __init__(self, window):

        self.window = window

    def run(self):

        initialize()

        WindowInitializer(

            self.window

        ).initialize()

        logger = getattr(
            getattr(self.window, "controller", None),
            "logger",
            None,
        )

        if logger:

            logger.log(

                "=" * 70

            )

            logger.log(

                "Audiobook Studio Started"

            )

            logger.log(

                "=" * 70

            )

    def self_test(self):

        from core.self_test import SelfTest

        SelfTest.run()