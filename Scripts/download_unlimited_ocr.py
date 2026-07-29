from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


MODEL_ID = "baidu/Unlimited-OCR"
MODEL_REVISION = "d549bb9d6a055dbe291408916d66acc2cd5920f6"
WEIGHT_NAME = "model-00001-of-000001.safetensors"
WEIGHT_SHA256 = "2bc48a7a110061ea58fff65d3169367eebe3aee371ca6968dc2219c1b2855fc6"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: download_unlimited_ocr.py MODEL_FOLDER", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {MODEL_ID} revision {MODEL_REVISION} to {target}")
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=str(target),
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    weight = target / WEIGHT_NAME
    if not weight.is_file():
        raise FileNotFoundError(f"Expected model weight is missing: {weight}")
    actual = sha256(weight)
    if actual.casefold() != WEIGHT_SHA256.casefold():
        raise RuntimeError(
            f"Unlimited-OCR weight hash mismatch. Expected {WEIGHT_SHA256}; found {actual}."
        )
    marker = {
        "schema": 1,
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "weight": WEIGHT_NAME,
        "sha256": actual,
    }
    (target / ".audiobookstudio_model_verified.json").write_text(
        json.dumps(marker, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print("Unlimited-OCR model verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
