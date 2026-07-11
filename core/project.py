from pathlib import Path

from core.parser import extract_book_text
from core.cleaner import clean_text
from core.chunker import split_into_chunks

from core.pronunciation import PronunciationDictionary
from core.replacer import Replacer
from core.chapters import detect_chapters

from core.generator import AudiobookGenerator
from core.merger import AudioMerger

from core.resume import ResumeManager
from core.library import Library
from core.statistics import Statistics
from core.logger import Logger


class AudiobookProject:

    def __init__(self):

        self.generator = AudiobookGenerator()

        self.merger = AudioMerger()

        self.resume = ResumeManager()

        self.library = Library()

        self.logger = Logger()

        self.dictionary = PronunciationDictionary()

        self.replacer = Replacer()

    def build(

        self,

        book,

        output_folder,

        voice,

        speed,

        pitch,

        progress_callback=None,

        status_callback=None,

        log_callback=None,

        statistics_callback=None,

        cancel_callback=None,

        pause_callback=None,

        export_mp3=False,

        export_m4b=False,

        delete_chunks=False,

        overwrite=False,

        replace_rules=None,

    ):

        book = Path(book)

        project = Path(output_folder) / book.stem

        project.mkdir(

            parents=True,

            exist_ok=True

        )

        self.library.add(book)

        if status_callback:

            status_callback(

                "Reading book..."

            )

        if log_callback:

            log_callback(

                f"Opening {book.name}"

            )

        text = extract_book_text(book)

        if cancel_callback and cancel_callback():

            return False

        if status_callback:

            status_callback(

                "Cleaning..."

            )

        text = clean_text(text)

        text = self.dictionary.replace(text)

        if replace_rules:

            self.replacer.set_rules(

                replace_rules

            )

            text = self.replacer.process(

                text

            )

        if status_callback:

            status_callback(

                "Detecting chapters..."

            )

        chapters = detect_chapters(text)

        if log_callback:

            log_callback(

                f"Detected {len(chapters)} chapters."

            )

        if status_callback:

            status_callback(

                "Creating chunks..."

            )

        chunks = split_into_chunks(text)

        total = len(chunks)

        if total == 0:

            raise RuntimeError(

                "No chunks generated."

            )

        if log_callback:

            log_callback(

                f"{total} chunks created."

            )

        if status_callback:

            status_callback(

                "Generating..."

            )

        success = self.generator.generate(

            title=book.stem,

            chunks=chunks,

            output_folder=project,

            voice=voice,

            speed=speed,

            pitch=pitch,

            overwrite=overwrite,

            progress_callback=progress_callback,

            log_callback=log_callback,

            cancel_callback=cancel_callback,

            statistics_callback=statistics_callback

        )

        if not success:

            return False

        if cancel_callback and cancel_callback():

            return False

        if pause_callback:

            pause_callback.wait()

        if status_callback:

            status_callback(

                "Merging..."

            )

        self.merger.merge(

            input_folder=project,

            output_file=project / "audiobook.wav",

            export_mp3=export_mp3,

            export_m4b=export_m4b,

            delete_chunks=delete_chunks,

            progress_callback=None,

            cancel_callback=cancel_callback

        )

        stats = Statistics.audiobook(

            project

        )

        self.library.update_progress(

            book,

            100

        )

        self.resume.remove(

            project

        )

        self.logger.write(

            f"Finished: {book.name}"

        )

        if log_callback:

            log_callback("")

            log_callback("=" * 70)

            log_callback("Generation Complete")

            log_callback("=" * 70)

            log_callback(

                f"Duration : {stats['duration']}"

            )

            log_callback(

                f"Size     : {stats['size']}"

            )

            log_callback("")

        if status_callback:

            status_callback(

                "Finished"

            )

        return True