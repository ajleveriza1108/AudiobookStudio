class ButtonState:
    """Tracks the minimum conditions required to start narration."""

    def __init__(self, generate):
        self.generate = generate
        self.book = False
        self.output = False
        self.engine = False
        self.refresh()

    def set_book(self, value):
        self.book = bool(value)
        self.refresh()

    def set_output(self, value):
        self.output = bool(value)
        self.refresh()

    def set_engine(self, value):
        self.engine = bool(value)
        self.refresh()

    def ready(self):
        return bool(self.book and self.output and self.engine)

    def refresh(self):
        self.generate.set_enabled(self.ready())
