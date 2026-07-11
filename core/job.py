from pathlib import Path
from datetime import datetime


class AudiobookJob:

    def __init__(

        self,

        source,

        output,

        voice,

        speed,

        pitch,

        engine,

    ):

        self.source = Path(source)

        self.output = Path(output)

        self.voice = voice

        self.speed = speed

        self.pitch = pitch

        self.engine = engine

        self.started = datetime.now()

        self.finished = None

        self.status = "Queued"

        self.progress = 0

    def running(self):

        self.status = "Running"

    def complete(self):

        self.status = "Completed"

        self.progress = 100

        self.finished = datetime.now()

    def failed(self):

        self.status = "Failed"

        self.finished = datetime.now()

    def cancelled(self):

        self.status = "Cancelled"

        self.finished = datetime.now()

    def eta(self):

        if self.progress <= 0:

            return None

        elapsed = (

            datetime.now()

            -

            self.started

        ).total_seconds()

        total = elapsed / (self.progress/100)

        remain = total-elapsed

        return max(0,int(remain))