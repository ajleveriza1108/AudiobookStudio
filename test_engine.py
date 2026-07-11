from __future__ import annotations

import argparse
import json
from pathlib import Path

from engines.factory import EngineFactory
from engines.manager import EngineManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check Audiobook Studio engines or generate a short test WAV."
    )
    parser.add_argument("--list", action="store_true", help="List engine status.")
    parser.add_argument("--engine", default="kokoro")
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--text", default="Audiobook Studio engine test.")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--pitch", type=float, default=0.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Output") / "engine_test.wav",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manager = EngineManager()

    if args.list:
        print(json.dumps(manager.available(), indent=2))
        return 0

    factory = EngineFactory(manager)
    engine = factory.load(args.engine)

    print(f"Engine:  {factory.current_name()}")
    print(f"Backend: {factory.backend()}")
    print(f"Device:  {factory.gpu()}")
    print(f"Voice:   {args.voice}")

    output = engine.speak(
        text=args.text,
        output_file=args.output,
        voice=args.voice,
        speed=args.speed,
        pitch=args.pitch,
    )
    print(f"Created: {output}")
    factory.unload()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
