import torch
import soundfile as sf
import numpy as np

from kokoro import KPipeline
from pathlib import Path


class KokoroEngine:

    def __init__(self):

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # stable single pipeline instance
        self.pipeline = KPipeline(lang_code="a")

    # =========================================================
    # REQUIRED BY BaseEngine (DO NOT REMOVE)
    # =========================================================
    def speak(self, text, output_file, voice, speed, pitch):

        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        audio_buffer = []
        sample_rate = 24000

        try:

            generator = self.pipeline(
                text,
                voice=voice,
                speed=speed
            )

            for item in generator:

                # robust unpacking (API-safe)
                try:
                    _, _, wav = item
                except Exception:
                    continue

                if wav is not None:
                    audio_buffer.extend(wav)

        except Exception as e:

            raise RuntimeError(f"Kokoro generation failed: {e}")

        if len(audio_buffer) == 0:

            raise RuntimeError("Empty audio generated")

        audio = np.array(audio_buffer, dtype=np.float32)

        # optional pitch shift (safe)
        if pitch != 0:

            factor = 2 ** (pitch / 12)

            idx = np.arange(0, len(audio), factor)

            idx = idx[idx < len(audio)]

            audio = np.interp(
                idx,
                np.arange(len(audio)),
                audio
            ).astype(np.float32)

        sf.write(output_file, audio, sample_rate)

        return str(output_file)

    # =========================================================
    # REQUIRED BY BaseEngine
    # =========================================================
    def available_voices(self):

        return ["af_heart"]

    # =========================================================
    def backend(self):

        return "CUDA" if torch.cuda.is_available() else "CPU"

    def gpu_name(self):

        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"