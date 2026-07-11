from pathlib import Path
from pydub import AudioSegment


class AudioMerger:

    def __init__(self):
        pass

    def merge(

        self,

        input_folder,
        output_file,

        export_mp3=False,
        export_m4b=False,

        bitrate="192k",
        delete_chunks=False,

        progress_callback=None,
        cancel_callback=None,

    ):

        input_folder = Path(input_folder)
        output_file = Path(output_file)

        wav_files = sorted(input_folder.glob("chunk_*.wav"))

        if not wav_files:
            raise RuntimeError("No audio chunks found for merging.")

        audiobook = AudioSegment.empty()

        total = len(wav_files)

        for index, wav in enumerate(wav_files):

            if cancel_callback and cancel_callback():
                return False

            try:

                segment = AudioSegment.from_wav(wav)

            except Exception as e:

                print(f"Skipping corrupted chunk: {wav.name} ({e})")
                continue

            audiobook += segment

            if progress_callback:

                try:
                    progress_callback(index + 1, total)
                except Exception:
                    pass

            print(f"[{index + 1}/{total}] merged {wav.name}")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # =========================
        # MAIN OUTPUT (WAV)
        # =========================
        audiobook.export(output_file, format="wav")

        # =========================
        # OPTIONAL EXPORTS
        # =========================
        if export_mp3:

            audiobook.export(
                output_file.with_suffix(".mp3"),
                format="mp3",
                bitrate=bitrate
            )

        if export_m4b:

            try:

                audiobook.export(
                    output_file.with_suffix(".m4b"),
                    format="mp4",
                    bitrate=bitrate
                )

            except Exception as e:

                print(f"M4B export skipped: {e}")

        # =========================
        # CLEANUP
        # =========================
        if delete_chunks:

            for wav in wav_files:

                try:
                    wav.unlink()
                except Exception:
                    pass

        print("\nMerge Finished.")

        return True