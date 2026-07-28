from __future__ import annotations

import contextlib
import json
import os
import sys
import traceback
from pathlib import Path


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def load_model(mode: str):
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    normalized = str(mode or "nano").strip().lower()

    with contextlib.redirect_stdout(sys.stderr):
        if normalized in {"nano", "turbo"}:
            from chatterbox.tts_turbo import ChatterboxTurboTTS

            model = ChatterboxTurboTTS.from_pretrained(
                device=device,
                nano=normalized == "nano",
            )
        elif normalized in {"multilingual", "multilingual-v3", "v3"}:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
            normalized = "multilingual-v3"
        else:
            from chatterbox.tts import ChatterboxTTS

            model = ChatterboxTTS.from_pretrained(device=device)
            normalized = "standard"

    return model, device, normalized


def save_audio(path: Path, waveform, sample_rate: int) -> None:
    import torchaudio as ta

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial.wav")
    with contextlib.redirect_stdout(sys.stderr):
        ta.save(str(temporary), waveform.cpu(), int(sample_rate))
    temporary.replace(path)


def main() -> int:
    model_mode = os.environ.get("AUDIOBOOK_STUDIO_CHATTERBOX_MODEL", "nano")
    try:
        model, device, model_mode = load_model(model_mode)
    except Exception as error:
        emit(
            {
                "type": "fatal",
                "error": str(error),
                "traceback": traceback.format_exc(),
            }
        )
        return 2

    emit(
        {
            "type": "ready",
            "engine": "chatterbox",
            "device": device,
            "model": model_mode,
            "sample_rate": int(getattr(model, "sr", 24000)),
        }
    )

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        request = {}
        try:
            request = json.loads(line)
            command = str(request.get("command", "synthesize"))
            request_id = str(request.get("id", ""))

            if command == "shutdown":
                emit({"type": "shutdown", "id": request_id, "ok": True})
                return 0
            if command != "synthesize":
                raise ValueError(f"Unknown command: {command}")

            text = str(request.get("text", "")).strip()
            sample = Path(str(request.get("speaker_wav", ""))).expanduser().resolve()
            output = Path(str(request.get("output_file", ""))).expanduser().resolve()
            language = str(request.get("language", "en") or "en").strip().lower()
            if not text:
                raise ValueError("Narration text is empty.")
            if not sample.is_file():
                raise FileNotFoundError(f"Reference recording not found: {sample}")

            kwargs = {"audio_prompt_path": str(sample)}
            if model_mode == "multilingual-v3":
                kwargs["language_id"] = language

            with contextlib.redirect_stdout(sys.stderr):
                waveform = model.generate(text, **kwargs)
            save_audio(output, waveform, int(getattr(model, "sr", 24000)))
            emit(
                {
                    "type": "result",
                    "id": request_id,
                    "ok": True,
                    "output_file": str(output),
                }
            )
        except Exception as error:
            emit(
                {
                    "type": "result",
                    "id": request.get("id", "") if isinstance(request, dict) else "",
                    "ok": False,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                }
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
