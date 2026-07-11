from __future__ import annotations

import compileall
import json
import sys
from pathlib import Path

from core.paths import PATHS
from engines.manager import EngineManager


def main() -> int:
    project_root = PATHS.project_root
    print(f"Project root: {project_root}")

    if not compileall.compile_dir(project_root, quiet=1):
        print("Python compilation check failed.", file=sys.stderr)
        return 1

    manager = EngineManager()
    print(json.dumps(manager.available(), indent=2))

    if manager.errors:
        print("Manifest errors:", file=sys.stderr)
        print(json.dumps(manager.errors, indent=2), file=sys.stderr)
        return 1

    print("Phase 1 verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
