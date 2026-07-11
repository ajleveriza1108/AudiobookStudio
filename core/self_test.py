from pathlib import Path

from core.environment import Environment


class SelfTest:

    @staticmethod
    def run():

        report = Environment.report()

        print("=" * 70)
        print("Audiobook Studio Self Test")
        print("=" * 70)

        for key, value in report.items():
            print(f"{key:12}: {value}")

        print()

        print("Engine")
        print("-" * 70)
        print("Kokoro : Deferred (lazy loaded)")
        print()

        folders = [
            "Books",
            "Models",
            "Output",
            "Temp",
            "Logs",
        ]

        print("Folders")
        print("-" * 70)

        for folder in folders:
            print(folder, Path(folder).exists())

        print()
        print("=" * 70)
        print("READY")
        print("=" * 70)