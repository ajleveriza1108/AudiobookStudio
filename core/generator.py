from __future__ import annotations

from pathlib import Path
import time

from core.chunk_validator import ChunkValidator
from core.engine_fingerprint import engine_fingerprint
from core.engine_service import EngineService
from core.resume import ResumeManager


class AudiobookGenerator:
    def __init__(self, engine="kokoro"):
        self.engine_name = str(engine or "kokoro")
        self.characters = 0
        self.words = 0
        self.generated = 0

    @staticmethod
    def _wait_if_paused(pause_callback, cancel_callback=None) -> bool:
        if pause_callback is None:
            return True

        # threading.Event is the established worker contract.
        while not pause_callback.is_set():
            if cancel_callback and cancel_callback():
                return False
            pause_callback.wait(0.2)
        return not (cancel_callback and cancel_callback())

    def generate(
        self,
        title,
        chunks,
        output_folder,
        voice,
        speed,
        pitch,
        engine=None,
        overwrite=False,
        progress_callback=None,
        log_callback=None,
        cancel_callback=None,
        pause_callback=None,
        statistics_callback=None,
        status_callback=None,
        resume_manager: ResumeManager | None = None,
        source_file: str | Path | None = None,
        text_hash: str = "",
    ):
        del title  # retained in the public signature for compatibility

        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        total = len(chunks)
        if total <= 0:
            raise RuntimeError("No narration sections were created.")

        selected_engine = str(engine or self.engine_name or "kokoro")
        settings = {
            "engine": selected_engine,
            "voice": str(voice),
            "speed": float(speed),
            "pitch": float(pitch),
            "engine_fingerprint": engine_fingerprint(selected_engine),
        }

        resume = resume_manager or ResumeManager(output_folder)
        resume.begin(
            total_chunks=total,
            source=source_file or output_folder,
            settings=settings,
            text_hash=text_hash,
        )

        self.generated = 0
        self.characters = sum(len(chunk) for chunk in chunks)
        self.words = sum(len(chunk.split()) for chunk in chunks)
        processed_characters = 0
        processed_words = 0
        started = time.monotonic()
        engine_instance = None

        for zero_index, chunk in enumerate(chunks):
            index = zero_index + 1

            if cancel_callback and cancel_callback():
                if log_callback:
                    log_callback("Generation stopped. Completed audio has been kept for resume.")
                return False

            if not self._wait_if_paused(pause_callback, cancel_callback):
                return False

            outfile = output_folder / f"chunk_{index:05d}.wav"
            reusable = not overwrite and resume.is_current(index, chunk, settings, outfile)

            if reusable:
                resume.mark_completed(index, total, chunk, settings, outfile)
                self.generated += 1
                processed_characters += len(chunk)
                processed_words += len(chunk.split())
                if log_callback:
                    log_callback(f"[{index}/{total}] Reused verified {outfile.name}")
            else:
                if outfile.exists():
                    outfile.unlink(missing_ok=True)

                if status_callback:
                    status_callback(f"Narrating section {index} of {total}")

                if engine_instance is None:
                    engine_instance = EngineService.load(selected_engine)

                try:
                    engine_instance.speak(
                        text=chunk,
                        output_file=outfile,
                        voice=voice,
                        speed=speed,
                        pitch=pitch,
                    )
                except Exception as error:
                    outfile.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"Narration stopped at section {index} of {total}: {error}"
                    ) from error

                if not ChunkValidator.valid(outfile):
                    outfile.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"Section {index} did not produce a valid audio file."
                    )

                resume.mark_completed(index, total, chunk, settings, outfile)
                self.generated += 1
                processed_characters += len(chunk)
                processed_words += len(chunk.split())

                if log_callback:
                    log_callback(f"[{index}/{total}] Created {outfile.name}")

            elapsed = max(time.monotonic() - started, 0.001)
            percent = int((self.generated / total) * 100)
            characters_per_second = int(processed_characters / elapsed)
            words_per_second = round(processed_words / elapsed, 2)
            remaining_sections = max(0, total - self.generated)
            average_section_time = elapsed / max(1, self.generated)
            eta_seconds = int(remaining_sections * average_section_time)

            if progress_callback:
                progress_callback(percent)

            if statistics_callback:
                statistics_callback(
                    {
                        "generated": self.generated,
                        "total": total,
                        "percent": percent,
                        "characters": processed_characters,
                        "words": processed_words,
                        "characters_per_second": characters_per_second,
                        "words_per_second": words_per_second,
                        "elapsed": int(elapsed),
                        "eta_seconds": eta_seconds,
                    }
                )

        return True
