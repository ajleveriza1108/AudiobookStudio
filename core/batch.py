from __future__ import annotations

from core.job import AudiobookJob


class JobCollection(list[AudiobookJob]):
    """List-compatible queue storage with legacy callable compatibility.

    Older AudiobookStudio UI files called ``batch.jobs()`` while newer files
    use ``batch.jobs`` as a list. Making the collection callable supports both
    forms, which prevents a partially updated installation from crashing.
    """

    def __call__(self) -> list[AudiobookJob]:
        return list(self)


class BatchProcessor:
    def __init__(self):
        self.jobs: JobCollection = JobCollection()

    def add(
        self,
        source,
        output,
        voice,
        speed,
        pitch,
        engine,
        chapter_plan=None,
        pronunciation_rules=None,
        metadata_overrides=None,
    ):
        job = AudiobookJob(
            source=source,
            output=output,
            voice=voice,
            speed=speed,
            pitch=pitch,
            engine=engine,
            chapter_plan=chapter_plan,
            pronunciation_rules=pronunciation_rules,
            metadata_overrides=metadata_overrides,
        )
        self.jobs.append(job)
        return job

    def remove(self, index):
        if 0 <= index < len(self.jobs):
            self.jobs.pop(index)

    def clear(self):
        self.jobs.clear()

    def next(self):
        return self.jobs.pop(0) if self.jobs else None

    def pending(self):
        return len(self.jobs)

    def all(self):
        return list(self.jobs)

    def empty(self):
        return not self.jobs
