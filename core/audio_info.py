from __future__ import annotations

from pathlib import Path
import wave


def get_audio_length(audio_file):
    path = Path(audio_file)
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        if rate <= 0:
            return 0.0
        return audio.getnframes() / rate


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining = seconds % 60
    return f"{hours:02}:{minutes:02}:{remaining:02}"


def folder_duration(folder):
    total = 0.0
    for wav in sorted(Path(folder).glob("chunk_*.wav")):
        try:
            total += get_audio_length(wav)
        except (OSError, wave.Error):
            continue
    return format_duration(total)
