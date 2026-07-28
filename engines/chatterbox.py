from __future__ import annotations

import atexit
import json
import os
import subprocess
import threading
import uuid
from pathlib import Path

import numpy as np
import soundfile as sf

from core.optional_engines import chatterbox_runtime_ready, voice_runtime_python
from core.paths import PATHS
from core.voice_library import VoiceLibrary
from engines.base import BaseEngine


class ChatterboxEngine(BaseEngine):
    """Optional isolated voice-cloning engine.

    Chatterbox is intentionally hosted in a separate virtual environment so it
    cannot destabilize the verified Kokoro/OCR runtime. Only user-authorized
    local voice profiles are accepted.
    """

    def __init__(self) -> None:
        if not chatterbox_runtime_ready():
            raise RuntimeError(
                "The optional Chatterbox module is not installed. "
                "Run install_voice_cloning.ps1, then reopen Audiobook Studio."
            )
        self.library = VoiceLibrary()
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.RLock()
        self._backend = "Not loaded"
        self._model = "nano"
        self._requested_model = ""
        self._log_stream = None
        atexit.register(self.unload)

    def _start(self, model_mode: str = "nano") -> None:
        requested = str(model_mode or "nano").strip().lower()
        if requested not in {"nano", "turbo", "multilingual-v3"}:
            requested = "nano"
        if (
            self._process is not None
            and self._process.poll() is None
            and self._requested_model == requested
        ):
            return
        if self._process is not None:
            self.unload()

        worker = PATHS.project_root / "Scripts" / "chatterbox_worker.py"
        python = voice_runtime_python()
        if not python.is_file() or not worker.is_file():
            raise RuntimeError("The optional voice-cloning runtime is incomplete.")

        PATHS.logs.mkdir(parents=True, exist_ok=True)
        self._log_stream = (PATHS.logs / "chatterbox_worker.log").open(
            "a", encoding="utf-8", buffering=1
        )
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        environment["HF_HOME"] = str(PATHS.models / "HuggingFace")
        environment["TORCH_HOME"] = str(PATHS.models / "Torch")
        environment["AUDIOBOOK_STUDIO_CHATTERBOX_MODEL"] = requested
        environment.setdefault("TRANSFORMERS_ATTN_IMPLEMENTATION", "eager")

        self._process = subprocess.Popen(
            [str(python), "-u", str(worker)],
            cwd=str(PATHS.project_root),
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._log_stream,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
        )

        ready = self._read_message()
        if ready.get("type") != "ready":
            error = ready.get("error") or "Voice-cloning worker did not become ready."
            self.unload()
            raise RuntimeError(str(error))
        self._backend = str(ready.get("device", "CPU")).upper()
        self._model = str(ready.get("model", requested))
        self._requested_model = requested

    def _read_message(self) -> dict:
        process = self._process
        if process is None or process.stdout is None:
            raise RuntimeError("Voice-cloning worker is not running.")
        while True:
            line = process.stdout.readline()
            if not line:
                code = process.poll()
                raise RuntimeError(
                    f"Voice-cloning worker stopped unexpectedly"
                    + (f" (exit code {code})." if code is not None else ".")
                )
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload

    @staticmethod
    def _post_process(path: Path, speed: float, pitch: float) -> None:
        selected_speed = max(0.5, min(2.0, float(speed)))
        selected_pitch = max(-12.0, min(12.0, float(pitch)))
        if abs(selected_speed - 1.0) < 0.001 and abs(selected_pitch) < 0.001:
            return

        import librosa

        audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
        if np.asarray(audio).ndim > 1:
            audio = np.mean(np.asarray(audio), axis=1)
        processed = np.asarray(audio, dtype=np.float32)
        if abs(selected_speed - 1.0) >= 0.001:
            processed = librosa.effects.time_stretch(processed, rate=selected_speed)
        if abs(selected_pitch) >= 0.001:
            processed = librosa.effects.pitch_shift(
                y=processed,
                sr=int(sample_rate),
                n_steps=selected_pitch,
            )
        peak = float(np.max(np.abs(processed))) if processed.size else 0.0
        if peak > 0.99:
            processed = processed * (0.99 / peak)
        temporary = path.with_name(path.name + ".processed.wav")
        sf.write(temporary, processed, int(sample_rate), subtype="PCM_16")
        temporary.replace(path)

    def speak(
        self,
        text: str,
        output_file: str | Path,
        voice: str,
        speed: float,
        pitch: float,
    ) -> str:
        content = str(text or "").strip()
        if not content:
            raise ValueError("Chatterbox cannot synthesize empty text.")
        profile = self.library.get(str(voice))
        if profile is None or not profile.authorized:
            raise RuntimeError(
                "Select an authorized local Voice Studio profile before using Chatterbox."
            )
        sample = self.library.sample_path(profile)
        if not sample.is_file():
            raise RuntimeError(f"Voice reference recording is missing: {sample}")

        output = Path(output_file).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        request_id = uuid.uuid4().hex

        with self._lock:
            self._start(profile.model)
            assert self._process is not None and self._process.stdin is not None
            request = {
                "command": "synthesize",
                "id": request_id,
                "text": content,
                "speaker_wav": str(sample),
                "language": profile.language,
                "output_file": str(output),
            }
            self._process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
            self._process.stdin.flush()

            while True:
                response = self._read_message()
                if response.get("type") == "result" and response.get("id") == request_id:
                    if not response.get("ok"):
                        raise RuntimeError(str(response.get("error") or "Voice cloning failed."))
                    break

        if not output.is_file() or output.stat().st_size < 256:
            raise RuntimeError("Chatterbox did not produce a valid WAV file.")
        self._post_process(output, speed, pitch)
        return str(output)

    def available_voices(self) -> list[str]:
        return self.library.ids(engine="chatterbox")

    def backend(self) -> str:
        return self._backend

    def gpu_name(self) -> str:
        return self._backend

    def capabilities(self) -> dict:
        return {
            "voice_cloning": True,
            "multilingual": True,
            "streaming": False,
            "pitch_control": True,
            "offline": True,
        }

    def unload(self) -> None:
        with self._lock:
            process = self._process
            self._process = None
            self._requested_model = ""
            if process is not None and process.poll() is None:
                try:
                    if process.stdin is not None:
                        process.stdin.write(json.dumps({"command": "shutdown", "id": "shutdown"}) + "\n")
                        process.stdin.flush()
                    process.wait(timeout=5)
                except Exception:
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
            if self._log_stream is not None:
                try:
                    self._log_stream.close()
                except Exception:
                    pass
                self._log_stream = None
