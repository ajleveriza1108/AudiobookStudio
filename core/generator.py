from pathlib import Path
import time
import traceback

from core.engine_service import EngineService


class AudiobookGenerator:

    def __init__(self, engine="kokoro"):

        self.engine_name = engine
        self.engine = EngineService.load(engine)

        self.characters = 0
        self.words = 0
        self.generated = 0

    def generate(

        self,

        title,

        chunks,

        output_folder,

        voice,

        speed,

        pitch,

        overwrite=False,

        progress_callback=None,

        log_callback=None,

        cancel_callback=None,

        statistics_callback=None,

    ):

        output_folder = Path(output_folder)

        output_folder.mkdir(

            parents=True,

            exist_ok=True

        )

        total = len(chunks)

        self.generated = 0

        self.characters = sum(

            len(x)

            for x in chunks

        )

        self.words = sum(

            len(x.split())

            for x in chunks

        )

        started = time.time()

        for index, chunk in enumerate(chunks):

            if cancel_callback:

                if cancel_callback():

                    if log_callback:

                        log_callback(

                            "Generation cancelled."

                        )

                    return False

            outfile = output_folder / f"chunk_{index+1:05d}.wav"

            if outfile.exists() and not overwrite:

                self.generated += 1

                percent = int(

                    self.generated

                    /

                    total

                    *

                    100

                )

                if progress_callback:

                    progress_callback(percent)

                continue

            try:

                self.engine.speak(

                    text=chunk,

                    output_file=outfile,

                    voice=voice,

                    speed=speed,

                    pitch=pitch

                )

                self.generated += 1

                elapsed = max(

                    time.time() - started,

                    0.001

                )

                cps = int(

                    self.characters

                    /

                    elapsed

                )

                wps = int(

                    self.words

                    /

                    elapsed

                )

                percent = int(

                    self.generated

                    /

                    total

                    *

                    100

                )

                if progress_callback:

                    progress_callback(

                        percent

                    )

                if statistics_callback:

                    statistics_callback({

                        "generated":

                            self.generated,

                        "total":

                            total,

                        "percent":

                            percent,

                        "characters":

                            self.characters,

                        "words":

                            self.words,

                        "characters_per_second":

                            cps,

                        "words_per_second":

                            wps,

                        "elapsed":

                            int(elapsed)

                    })

                if log_callback:

                    log_callback(

                        f"[{self.generated}/{total}] chunk_{index+1:05d}.wav"

                    )

            except Exception:

                if log_callback:

                    log_callback(

                        traceback.format_exc()

                    )

                return False

        return True