from __future__ import annotations

import gc
import os
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

from engines.base import BaseEngine


class KokoroEngine(BaseEngine):
    SAMPLE_RATE = 24000
    DEFAULT_VOICE = "af_heart"

    COMMON_VOICES = [
        "af_heart",
        "af_alloy",
        "af_aoede",
        "af_bella",
        "af_jessica",
        "af_kore",
        "af_nicole",
        "af_nova",
        "af_river",
        "af_sarah",
        "af_sky",
        "am_adam",
        "am_echo",
        "am_eric",
        "am_fenrir",
        "am_liam",
        "am_michael",
        "am_onyx",
        "am_puck",
        "am_santa",
        "bf_alice",
        "bf_emma",
        "bf_isabella",
        "bf_lily",
        "bm_daniel",
        "bm_fable",
        "bm_george",
        "bm_lewis",
    ]

    def __init__(
        self,
        lang_code: str = "a",
        device: str | None = None,
        sample_rate: int = SAMPLE_RATE,
    ) -> None:
        self.lang_code = str(lang_code or "a")
        self.sample_rate = int(sample_rate)
        self.device = device or self._preferred_device()
        self.pipeline = None

    @staticmethod
    def _preferred_device() -> str:
        requested = os.getenv("AUDIOBOOK_STUDIO_DEVICE", "").strip().lower()
        if requested in {"cpu", "cuda"}:
            return requested

        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _ensure_pipeline(self):
        if self.pipeline is not None:
            return self.pipeline

        try:
            from kokoro import KPipeline
        except ImportError as error:
            raise RuntimeError(
                "Kokoro is not installed. Run: pip install kokoro>=0.9.4 soundfile"
            ) from error

        try:
            self.pipeline = KPipeline(lang_code=self.lang_code)
            model = getattr(self.pipeline, "model", None)
            if model is not None and hasattr(model, "to"):
                model.to(self.device)
        except Exception as error:
            self.pipeline = None
            raise RuntimeError(f"Could not initialize Kokoro: {error}") from error

        return self.pipeline

    @staticmethod
    def _to_numpy(value: Any) -> np.ndarray | None:
        if value is None:
            return None

        if hasattr(value, "detach"):
            value = value.detach()
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "numpy"):
            value = value.numpy()

        try:
            array = np.asarray(value, dtype=np.float32).reshape(-1)
        except Exception:
            return None

        if array.size == 0:
            return None
        return array

    @classmethod
    def _extract_audio(cls, item: Any) -> np.ndarray | None:
        audio = getattr(item, "audio", None)
        if audio is not None:
            return cls._to_numpy(audio)

        if isinstance(item, (tuple, list)):
            for value in reversed(item):
                array = cls._to_numpy(value)
                if array is not None and array.size > 32:
                    return array
            return None

        return cls._to_numpy(item)

    def _apply_pitch(self, audio: np.ndarray, semitones: float) -> np.ndarray:
        if abs(semitones) < 0.001:
            return audio

        try:
            import librosa
        except ImportError as error:
            raise RuntimeError(
                "Pitch control requires librosa. Run: pip install librosa"
            ) from error

        shifted = librosa.effects.pitch_shift(
            y=audio,
            sr=self.sample_rate,
            n_steps=float(semitones),
        )
        return np.asarray(shifted, dtype=np.float32)

    @staticmethod
    def _normalize(audio: np.ndarray) -> np.ndarray:
        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0

        if peak > 0.99:
            audio = audio * (0.99 / peak)

        return np.asarray(audio, dtype=np.float32)

    def speak(
        self,
        text: str,
        output_file: str | Path,
        voice: str = DEFAULT_VOICE,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> str:
        content = str(text or "").strip()
        if not content:
            raise ValueError("Kokoro cannot synthesize empty text.")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        selected_voice = str(voice or self.DEFAULT_VOICE)
        selected_speed = max(0.5, min(2.0, float(speed)))
        selected_pitch = max(-12.0, min(12.0, float(pitch)))

        pipeline = self._ensure_pipeline()
        parts: list[np.ndarray] = []

        try:
            generated = pipeline(
                content,
                voice=selected_voice,
                speed=selected_speed,
            )

            for item in generated:
                audio = self._extract_audio(item)
                if audio is not None:
                    parts.append(audio)
        except Exception as error:
            raise RuntimeError(f"Kokoro generation failed: {error}") from error

        if not parts:
            raise RuntimeError("Kokoro returned no audio.")

        audio = np.concatenate(parts)
        audio = self._apply_pitch(audio, selected_pitch)
        audio = self._normalize(audio)

        if audio.size < int(self.sample_rate * 0.05):
            raise RuntimeError("Kokoro returned an audio chunk that is too short.")

        temporary = output_path.with_name(output_path.name + ".partial")
        try:
            sf.write(
                temporary,
                audio,
                self.sample_rate,
                format="WAV",
                subtype="PCM_16",
            )
            temporary.replace(output_path)
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)

        return str(output_path)

    def available_voices(self) -> list[str]:
        return list(self.COMMON_VOICES)

    def backend(self) -> str:
        return "CUDA" if self.device == "cuda" else "CPU"

    def gpu_name(self) -> str:
        if self.device != "cuda":
            return "CPU"

        try:
            import torch

            return str(torch.cuda.get_device_name(0))
        except Exception:
            return "CUDA"

    def capabilities(self) -> dict[str, Any]:
        return {
            "voice_cloning": False,
            "multilingual": True,
            "streaming": True,
            "pitch_control": True,
            "sample_rate": self.sample_rate,
            "language_code": self.lang_code,
        }

    def health_check(self) -> dict[str, Any]:
        try:
            import kokoro  # noqa: F401
            import soundfile  # noqa: F401

            dependencies_ok = True
            error = ""
        except Exception as dependency_error:
            dependencies_ok = False
            error = str(dependency_error)

        return {
            "ok": dependencies_ok,
            "engine": "kokoro",
            "backend": self.backend(),
            "gpu": self.gpu_name(),
            "voices": len(self.COMMON_VOICES),
            "pipeline_loaded": self.pipeline is not None,
            "error": error,
        }

    def unload(self) -> None:
        self.pipeline = None
        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
