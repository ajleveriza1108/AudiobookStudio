from __future__ import annotations

from pathlib import Path

from core.audio_info import folder_duration, format_duration, get_audio_length
from core.utils import folder_size


class Statistics:
    @staticmethod
    def _encoded_duration(folder: Path) -> str | None:
        for name in ("audiobook.mp3", "audiobook.m4b"):
            path = folder / name
            if not path.is_file():
                continue
            try:
                from mutagen import File

                media = File(path)
                length = float(getattr(getattr(media, "info", None), "length", 0.0))
                if length > 0:
                    return format_duration(length)
            except Exception:
                continue
        return None

    @staticmethod
    def audiobook(folder):
        path = Path(folder)
        duration = None

        final_wav = path / "audiobook.wav"
        if final_wav.is_file():
            try:
                duration = format_duration(get_audio_length(final_wav))
            except Exception:
                duration = None

        if not duration:
            duration = Statistics._encoded_duration(path)

        if not duration:
            duration = folder_duration(path)

        return {
            "duration": duration,
            "size": folder_size(path),
            "chunks": len(list(path.glob("chunk_*.wav"))),
        }
