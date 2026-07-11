from pathlib import Path
from pydub import AudioSegment


class Media:

    @staticmethod
    def duration_seconds(audio_file):

        audio = AudioSegment.from_file(audio_file)

        return len(audio) / 1000

    @staticmethod
    def folder_duration(folder):

        total = 0

        folder = Path(folder)

        for wav in sorted(folder.glob("chunk_*.wav")):

            total += Media.duration_seconds(wav)

        return total

    @staticmethod
    def format_duration(seconds):

        h = int(seconds // 3600)

        m = int((seconds % 3600) // 60)

        s = int(seconds % 60)

        return f"{h:02}:{m:02}:{s:02}"

    @staticmethod
    def estimate_output_size(duration_seconds, bitrate=192):

        mb = (duration_seconds * bitrate * 1000) / 8 / 1024 / 1024

        return round(mb, 2)

    @staticmethod
    def merge_duration(folder):

        seconds = Media.folder_duration(folder)

        return Media.format_duration(seconds)