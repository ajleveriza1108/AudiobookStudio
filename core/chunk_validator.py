from __future__ import annotations

from pathlib import Path
import re
import wave


class ChunkValidator:
    CHUNK_NAME = re.compile(r"^chunk_(\d{5})\.wav$", re.IGNORECASE)

    @classmethod
    def number(cls, file) -> int | None:
        match = cls.CHUNK_NAME.match(Path(file).name)
        return int(match.group(1)) if match else None

    @classmethod
    def ordered(cls, folder) -> list[Path]:
        root = Path(folder)
        numbered = []
        for path in root.glob("chunk_*.wav"):
            number = cls.number(path)
            if number is not None:
                numbered.append((number, path))
        numbered.sort(key=lambda item: item[0])
        return [path for _, path in numbered]

    @staticmethod
    def exists(file):
        return Path(file).is_file()

    @staticmethod
    def inspect(file) -> dict:
        path = Path(file)
        result = {
            "valid": False,
            "frames": 0,
            "sample_rate": 0,
            "channels": 0,
            "sample_width": 0,
            "size": 0,
        }

        if not path.is_file():
            return result

        try:
            result["size"] = path.stat().st_size
            with wave.open(str(path), "rb") as wav:
                result.update(
                    {
                        "frames": wav.getnframes(),
                        "sample_rate": wav.getframerate(),
                        "channels": wav.getnchannels(),
                        "sample_width": wav.getsampwidth(),
                    }
                )
        except (OSError, wave.Error):
            return result

        result["valid"] = bool(
            result["size"] > 4096
            and result["frames"] > 0
            and result["sample_rate"] > 0
            and result["channels"] > 0
            and result["sample_width"] > 0
        )
        return result

    @staticmethod
    def valid(file):
        return bool(ChunkValidator.inspect(file)["valid"])

    @staticmethod
    def remove_invalid(file):
        path = Path(file)
        if path.exists() and not ChunkValidator.valid(path):
            path.unlink(missing_ok=True)
