from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Real Windows GUI startup probe")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--visible-ms", type=int, default=8000)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    if os.name != "nt":
        print("Real Windows GUI startup probe: SKIPPED (not Windows)")
        return 0

    marker = root / "Logs" / "gui_probe_complete.json"
    try:
        if marker.exists():
            marker.unlink()
    except OSError:
        pass

    env = dict(os.environ)
    env.pop("QT_QPA_PLATFORM", None)
    env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "CUDA_VISIBLE_DEVICES": "",
            "AUDIOBOOK_STUDIO_DEVICE": "cpu",
            "AUDIOBOOK_STUDIO_PROBE": "1",
            # app.py starts this dwell only after the previous book restore has
            # finished, so a slow scanned PDF cannot hide a delayed paint crash.
            "AUDIOBOOK_STUDIO_AUTO_EXIT_MS": str(max(3000, args.visible_ms)),
            "QT_STYLE_OVERRIDE": "Fusion",
            "QT_OPENGL": "software",
            "QT_QUICK_BACKEND": "software",
            "QSG_RHI_BACKEND": "software",
            "QT_WIDGETS_RHI": "0",
        }
    )

    try:
        completed = subprocess.run(
            [sys.executable, "-u", "app.py"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(30, args.timeout),
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        print("Real Windows GUI startup probe timed out.", file=sys.stderr)
        if error.stdout:
            print(error.stdout, file=sys.stderr)
        if error.stderr:
            print(error.stderr, file=sys.stderr)
        return 124

    if completed.stdout.strip():
        print(completed.stdout.rstrip())
    if completed.stderr.strip():
        print(completed.stderr.rstrip(), file=sys.stderr)

    if completed.returncode != 0:
        print(
            f"Real Windows GUI startup probe failed with exit code {completed.returncode}.",
            file=sys.stderr,
        )
        return completed.returncode or 1

    if not marker.is_file():
        print(
            "Real Windows GUI startup probe exited without completing the post-restore visible dwell.",
            file=sys.stderr,
        )
        return 3
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"GUI probe marker is unreadable: {error}", file=sys.stderr)
        return 4
    if payload.get("stage") != "post-restore-visible-dwell-complete":
        print("GUI probe marker did not confirm the required stage.", file=sys.stderr)
        return 5

    print("Real Windows GUI post-restore paint probe: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
