from pathlib import Path

from core.job import AudiobookJob


class BatchProcessor:

    def __init__(self):

        self.jobs = []

    def add(

        self,

        source,

        output,

        voice,

        speed,

        pitch,

        engine

    ):

        job = AudiobookJob(

            source=source,

            output=output,

            voice=voice,

            speed=speed,

            pitch=pitch,

            engine=engine

        )

        self.jobs.append(job)

        return job

    def remove(

        self,

        index

    ):

        if index < 0:

            return

        if index >= len(self.jobs):

            return

        self.jobs.pop(index)

    def clear(self):

        self.jobs.clear()

    def next(self):

        if len(self.jobs) == 0:

            return None

        return self.jobs.pop(0)

    def pending(self):

        return len(self.jobs)

    def all(self):

        return self.jobs

    def empty(self):

        return len(self.jobs) == 0