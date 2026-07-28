from __future__ import annotations

from pathlib import Path
import wave
from typing import Any

from core.chapter_timing import build_chapter_timings, write_ffmetadata
from core.chunk_validator import ChunkValidator
from core.ffmpeg import FFmpeg


class AudioMerger:
    @staticmethod
    def _emit_progress(callback, index: int, total: int) -> None:
        if not callback:
            return
        try:
            callback(index, total)
        except TypeError:
            callback(int((index / max(1, total)) * 100))

    @staticmethod
    def _wait_if_paused(pause_callback, cancel_callback=None) -> bool:
        if pause_callback is None:
            return True
        while not pause_callback.is_set():
            if cancel_callback and cancel_callback():
                return False
            pause_callback.wait(0.2)
        return not (cancel_callback and cancel_callback())

    @staticmethod
    def _merge_wav_files(
        wav_files: list[Path],
        output_file: Path,
        progress_callback=None,
        cancel_callback=None,
        pause_callback=None,
    ) -> bool:
        first_details = ChunkValidator.inspect(wav_files[0])
        if not first_details["valid"]:
            raise RuntimeError(f"Audio section is damaged: {wav_files[0].name}")

        temporary = output_file.with_name(output_file.name + ".partial")
        temporary.unlink(missing_ok=True)

        try:
            with wave.open(str(wav_files[0]), "rb") as first:
                parameters = first.getparams()

            with wave.open(str(temporary), "wb") as destination:
                destination.setnchannels(parameters.nchannels)
                destination.setsampwidth(parameters.sampwidth)
                destination.setframerate(parameters.framerate)
                destination.setcomptype(parameters.comptype, parameters.compname)

                for index, wav_file in enumerate(wav_files, start=1):
                    if cancel_callback and cancel_callback():
                        return False
                    if not AudioMerger._wait_if_paused(pause_callback, cancel_callback):
                        return False

                    details = ChunkValidator.inspect(wav_file)
                    if not details["valid"]:
                        raise RuntimeError(f"Audio section is damaged: {wav_file.name}")

                    with wave.open(str(wav_file), "rb") as source:
                        current = source.getparams()
                        if (
                            current.nchannels != parameters.nchannels
                            or current.sampwidth != parameters.sampwidth
                            or current.framerate != parameters.framerate
                            or current.comptype != parameters.comptype
                        ):
                            raise RuntimeError(
                                f"Audio section uses a different format: {wav_file.name}"
                            )

                        while True:
                            frames = source.readframes(65536)
                            if not frames:
                                break
                            destination.writeframesraw(frames)

                    AudioMerger._emit_progress(progress_callback, index, len(wav_files))

            temporary.replace(output_file)
            return True
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _metadata_arguments(metadata: dict[str, Any] | None) -> list[str]:
        data = metadata or {}
        fields = {
            "title": data.get("title"),
            "artist": data.get("author"),
            "album": data.get("title"),
            "composer": data.get("narrator"),
            "genre": data.get("genre", "Audiobook"),
            "comment": data.get("description"),
            "date": data.get("year"),
        }
        arguments: list[str] = []
        for key, value in fields.items():
            if value not in (None, "", "Unknown"):
                arguments.extend(["-metadata", f"{key}={value}"])
        return arguments

    @staticmethod
    def _export_mp3(
        source: Path,
        destination: Path,
        bitrate: str,
        metadata: dict[str, Any] | None = None,
        cover: Path | None = None,
    ) -> None:
        base = [
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
        ]
        if cover and cover.is_file():
            arguments = base + [
                "-i",
                str(cover),
                "-map",
                "0:a:0",
                "-map",
                "1:v:0",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                bitrate,
                "-codec:v",
                "mjpeg",
                "-id3v2_version",
                "3",
                "-metadata:s:v",
                "title=Album cover",
                "-metadata:s:v",
                "comment=Cover (front)",
                "-disposition:v",
                "attached_pic",
                *AudioMerger._metadata_arguments(metadata),
                str(destination),
            ]
            try:
                FFmpeg.run(arguments)
                return
            except RuntimeError:
                # Some FFmpeg builds reject a particular cover image codec.
                # Preserve the export by retrying without artwork.
                destination.unlink(missing_ok=True)

        FFmpeg.run(
            base
            + [
                "-codec:a",
                "libmp3lame",
                "-b:a",
                bitrate,
                *AudioMerger._metadata_arguments(metadata),
                str(destination),
            ]
        )

    @staticmethod
    def _export_m4b(
        source: Path,
        destination: Path,
        bitrate: str,
        metadata: dict[str, Any],
        chapters: list[dict[str, Any]],
        cover: Path | None = None,
    ) -> None:
        ffmetadata = destination.with_suffix(".ffmetadata.txt")
        write_ffmetadata(ffmetadata, metadata, chapters)
        try:
            base = [
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-i",
                str(ffmetadata),
            ]
            if cover and cover.is_file():
                arguments = base + [
                    "-i",
                    str(cover),
                    "-map",
                    "0:a:0",
                    "-map",
                    "2:v:0",
                    "-map_metadata",
                    "1",
                    "-map_chapters",
                    "1",
                    "-codec:a",
                    "aac",
                    "-b:a",
                    bitrate,
                    "-codec:v",
                    "mjpeg",
                    "-disposition:v",
                    "attached_pic",
                    "-metadata:s:v",
                    "title=Cover",
                    "-metadata",
                    "media_type=2",
                    "-movflags",
                    "+faststart",
                    str(destination),
                ]
                try:
                    FFmpeg.run(arguments)
                    return
                except RuntimeError:
                    destination.unlink(missing_ok=True)

            FFmpeg.run(
                base
                + [
                    "-map",
                    "0:a:0",
                    "-map_metadata",
                    "1",
                    "-map_chapters",
                    "1",
                    "-codec:a",
                    "aac",
                    "-b:a",
                    bitrate,
                    "-metadata",
                    "media_type=2",
                    "-movflags",
                    "+faststart",
                    str(destination),
                ]
            )
        finally:
            ffmetadata.unlink(missing_ok=True)

    def merge(
        self,
        input_folder,
        output_file,
        export_wav=True,
        export_mp3=False,
        export_m4b=False,
        bitrate="192k",
        delete_chunks=False,
        progress_callback=None,
        cancel_callback=None,
        pause_callback=None,
        title: str | None = None,
        expected_total: int | None = None,
        metadata: dict[str, Any] | None = None,
        chapter_map: list[dict[str, Any]] | None = None,
        cover_file: str | Path | None = None,
    ):
        input_folder = Path(input_folder)
        output_file = Path(output_file)
        wav_files = ChunkValidator.ordered(input_folder)

        if not wav_files:
            raise RuntimeError("No narration sections were found for merging.")

        if expected_total is not None and len(wav_files) != int(expected_total):
            raise RuntimeError(
                f"Expected {int(expected_total)} narration sections but found {len(wav_files)}."
            )

        for wav_file in wav_files:
            if not ChunkValidator.valid(wav_file):
                raise RuntimeError(
                    f"A narration section is missing or damaged: {wav_file.name}"
                )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        merged = self._merge_wav_files(
            wav_files,
            output_file,
            progress_callback=progress_callback,
            cancel_callback=cancel_callback,
            pause_callback=pause_callback,
        )
        if not merged:
            output_file.unlink(missing_ok=True)
            return False

        media_metadata = dict(metadata or {})
        media_metadata.setdefault("title", title or output_file.stem)
        cover = Path(cover_file) if cover_file else None
        chapter_timings = build_chapter_timings(input_folder, chapter_map)

        completed_outputs = [output_file]
        try:
            if export_mp3:
                mp3 = output_file.with_suffix(".mp3")
                self._export_mp3(output_file, mp3, bitrate, media_metadata, cover)
                completed_outputs.append(mp3)

            if export_m4b:
                m4b = output_file.with_suffix(".m4b")
                self._export_m4b(
                    output_file,
                    m4b,
                    bitrate,
                    media_metadata,
                    chapter_timings,
                    cover,
                )
                completed_outputs.append(m4b)
        except Exception:
            # Keep the verified WAV so compressed export can be retried without
            # regenerating the entire book.
            raise

        if not export_wav:
            output_file.unlink(missing_ok=True)
            completed_outputs = [item for item in completed_outputs if item != output_file]

        if delete_chunks:
            for wav_file in wav_files:
                wav_file.unlink(missing_ok=True)

        return bool(completed_outputs)
