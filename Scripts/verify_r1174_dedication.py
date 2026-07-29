from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import fitz

from core.ocr_corrections import find_correction_profile


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the R1.17.4 dedication-page correction profile."
    )
    parser.add_argument("pdf", help="Path to the scanned PDF")
    args = parser.parse_args()

    source = Path(args.pdf).expanduser().resolve()
    if not source.is_file():
        print(f"FAIL: PDF not found: {source}")
        return 2

    with fitz.open(source) as document:
        pages = int(document.page_count)
    profile = find_correction_profile(source, page_count=pages)
    if profile is None:
        print("FAIL: No verified correction profile matches this PDF.")
        return 3

    page_two = profile.page_text(2) or ""
    expected = (
        "Remember When, 1945. To Dad. From Dan and Diana. "
        "Date: August seventh, twenty twenty-six. "
        "The richness of life lies in the memories we have forgotten."
    )
    if page_two != expected:
        print("FAIL: Page 2 narration does not match the approved script.")
        print(page_two)
        return 4

    print("PASS: Verified correction profile:", profile.profile_id)
    print("PASS: Page 2 narration:")
    print(page_two)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
