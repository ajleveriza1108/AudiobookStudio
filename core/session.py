from datetime import datetime


class Session:

    def __init__(self):

        self.started = datetime.now()

        self.book = None

        self.engine = "kokoro"

        self.voice = None

        self.output = None

        self.speed = 1.0

        self.pitch = 0

        self.generated_chunks = 0

        self.total_chunks = 0

    def percentage(self):

        if self.total_chunks == 0:

            return 0

        return int(

            self.generated_chunks

            /

            self.total_chunks

            *

            100

        )

    def elapsed(self):

        return (

            datetime.now()

            -

            self.started

        ).total_seconds()