from __future__ import annotations

import contextlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def newest_text_file(folder: Path) -> Path | None:
    candidates = [
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".mmd", ".txt"}
    ]
    return max(candidates, key=lambda item: item.stat().st_mtime_ns, default=None)


def extract_text(result: Any, output_dir: Path) -> tuple[str, str]:
    if isinstance(result, str) and result.strip():
        possible = Path(result)
        if possible.is_file():
            return possible.read_text(encoding="utf-8-sig", errors="replace"), str(possible)
        if len(result.split()) >= 3:
            return result, "return-value"
    if isinstance(result, dict):
        for key in ("text", "markdown", "result", "output"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value, f"return-dict:{key}"
    text_file = newest_text_file(output_dir)
    if text_file is None:
        return "", ""
    return text_file.read_text(encoding="utf-8-sig", errors="replace"), str(text_file)


def load_model():
    import torch
    from transformers import AutoModel, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available in the Advanced OCR runtime.")
    if hasattr(torch.cuda, "is_bf16_supported") and not torch.cuda.is_bf16_supported():
        raise RuntimeError("The detected GPU does not support the BF16 model safely.")
    model_dir = Path(
        os.environ.get("AUDIOBOOK_STUDIO_UNLIMITED_OCR_MODEL", "Models/Unlimited-OCR")
    ).expanduser().resolve()
    if not (model_dir / "config.json").is_file():
        raise FileNotFoundError(f"Unlimited-OCR model files are missing: {model_dir}")
    with contextlib.redirect_stdout(sys.stderr):
        tokenizer = AutoTokenizer.from_pretrained(
            str(model_dir), trust_remote_code=True, local_files_only=True
        )
        model = AutoModel.from_pretrained(
            str(model_dir),
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )
        model = model.eval().cuda()
    return model, tokenizer, model_dir, torch.cuda.get_device_name(0)


def main() -> int:
    emit({"type": "status", "stage": "loading", "message": "Loading Advanced OCR model"})
    try:
        model, tokenizer, model_dir, device = load_model()
    except Exception as error:
        emit({"type": "fatal", "error": str(error), "traceback": traceback.format_exc()})
        return 2
    emit(
        {
            "type": "ready",
            "engine": "unlimited-ocr",
            "device": device,
            "model": str(model_dir),
        }
    )

    for raw_line in sys.stdin:
        request: dict[str, Any] = {}
        try:
            request = json.loads(raw_line)
            request_id = str(request.get("id") or "")
            command = str(request.get("command") or "recognize")
            if command == "shutdown":
                emit({"type": "shutdown", "id": request_id, "ok": True})
                return 0
            if command != "recognize":
                raise ValueError(f"Unknown Advanced OCR command: {command}")
            image = Path(str(request.get("image_file") or "")).expanduser().resolve()
            output_dir = Path(str(request.get("output_dir") or "")).expanduser().resolve()
            if not image.is_file():
                raise FileNotFoundError(f"OCR page image was not found: {image}")
            output_dir.mkdir(parents=True, exist_ok=True)
            emit({"type": "status", "id": request_id, "stage": "recognizing"})
            with contextlib.redirect_stdout(sys.stderr):
                result = model.infer(
                    tokenizer,
                    prompt="<image>document parsing.",
                    image_file=str(image),
                    output_path=str(output_dir),
                    base_size=1024,
                    image_size=640,
                    crop_mode=True,
                    max_length=16384,
                    no_repeat_ngram_size=35,
                    ngram_window=128,
                    save_results=True,
                )
            text, source_file = extract_text(result, output_dir)
            if not text.strip():
                raise RuntimeError("Unlimited-OCR completed without a readable text result.")
            emit(
                {
                    "type": "result",
                    "id": request_id,
                    "ok": True,
                    "text": text,
                    "source_file": source_file,
                    "device": device,
                    "model": str(model_dir),
                }
            )
        except Exception as error:
            emit(
                {
                    "type": "result",
                    "id": str(request.get("id") or ""),
                    "ok": False,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
