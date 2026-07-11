from pathlib import Path
import wave


class AudioValidator:

    @staticmethod
    def is_valid(file):

        file = Path(file)

        if not file.exists():
            return False

        if file.stat().st_size < 4096:
            return False

        try:

            with wave.open(str(file), "rb") as wav:

                if wav.getnframes() <= 0:
                    return False

                if wav.getframerate() <= 0:
                    return False

                if wav.getnchannels() <= 0:
                    return False

        except Exception:

            return False

        return True

    @staticmethod
    def validate_folder(folder):

        folder = Path(folder)

        good = []
        bad = []

        for wav in sorted(folder.glob("*.wav")):

            if AudioValidator.is_valid(wav):

                good.append(wav)

            else:

                bad.append(wav)

        return good, bad

    @staticmethod
    def remove_invalid(folder):

        _, bad = AudioValidator.validate_folder(folder)

        for wav in bad:

            try:

                wav.unlink()

            except Exception:

                pass

        return len(bad)