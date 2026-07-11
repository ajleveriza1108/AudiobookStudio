from pathlib import Path

from pydub import AudioSegment


def get_audio_length(audio_file):

    audio = AudioSegment.from_file(

        audio_file

    )

    return len(audio) / 1000


def format_duration(seconds):

    h = int(seconds // 3600)

    m = int((seconds % 3600) // 60)

    s = int(seconds % 60)

    return f"{h:02}:{m:02}:{s:02}"


def folder_duration(folder):

    total = 0

    folder = Path(folder)

    for wav in sorted(

        folder.glob("chunk_*.wav")

    ):

        total += get_audio_length(

            wav

        )

    return format_duration(total)