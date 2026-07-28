from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from core.paths import PATHS


class FFmpeg:
    @staticmethod
    def executable() -> str | None:
        candidates = [
            PATHS.project_root / "ffmpeg.exe",
            PATHS.project_root / "Scripts" / "ffmpeg.exe",
            PATHS.project_root / "FFmpeg" / "bin" / "ffmpeg.exe",
            PATHS.project_root / "Tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            PATHS.project_root / "Scripts" / "ffmpeg" / "bin" / "ffmpeg.exe",
        ]

        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

        return shutil.which("ffmpeg")

    @staticmethod
    def exists() -> bool:
        return FFmpeg.executable() is not None

    @staticmethod
    def version():
        executable = FFmpeg.executable()
        if not executable:
            return None

        try:
            result = subprocess.run(
                [executable, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.stdout.splitlines()[0] if result.stdout else None
        except (OSError, subprocess.SubprocessError):
            return None

    @staticmethod
    def run(arguments: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
        executable = FFmpeg.executable()
        if not executable:
            raise RuntimeError(
                "FFmpeg was not found. WAV export is available, but MP3 and M4B require FFmpeg."
            )

        result = subprocess.run(
            [executable, *arguments],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            details = (result.stderr or result.stdout or "FFmpeg failed.").strip()
            raise RuntimeError(details[-2000:])

        return result
