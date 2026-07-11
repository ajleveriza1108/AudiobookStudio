from PySide6.QtCore import QObject, Signal


class ProgressManager(QObject):

    progress_changed = Signal(int)

    overall_changed = Signal(int)

    eta_changed = Signal(str)

    status_changed = Signal(str)

    chunk_changed = Signal(str)

    chapter_changed = Signal(str)

    def __init__(self):

        super().__init__()

        self.total_chunks = 0

        self.current_chunk = 0

    def start(

        self,

        total,

    ):

        self.total_chunks = total

        self.current_chunk = 0

        self.progress_changed.emit(

            0,

        )

        self.overall_changed.emit(

            0,

        )

    def update(

        self,

        chunk,

    ):

        self.current_chunk = chunk

        if self.total_chunks <= 0:

            return

        percent = int(

            (

                self.current_chunk

                /

                self.total_chunks

            )

            *

            100

        )

        self.progress_changed.emit(

            percent,

        )

    def status(

        self,

        text,

    ):

        self.status_changed.emit(

            text,

        )

    def eta(

        self,

        text,

    ):

        self.eta_changed.emit(

            text,

        )

    def chapter(

        self,

        text,

    ):

        self.chapter_changed.emit(

            text,

        )

    def chunk(

        self,

        text,

    ):

        self.chunk_changed.emit(

            text,

        )

    def finish(self):

        self.progress_changed.emit(

            100,

        )

        self.overall_changed.emit(

            100,

        )

        self.status_changed.emit(

            "Completed",

        )