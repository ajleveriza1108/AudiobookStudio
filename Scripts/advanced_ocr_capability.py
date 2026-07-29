from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.advanced_ocr import AdvancedOCRCompatibility  # noqa: E402


def main() -> int:
    report = AdvancedOCRCompatibility.check_and_record(project_root=PROJECT_ROOT)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    status = str(report.get("status") or "unsupported")
    return 0 if status == "supported" else (3 if status == "experimental" else 4)


if __name__ == "__main__":
    raise SystemExit(main())
