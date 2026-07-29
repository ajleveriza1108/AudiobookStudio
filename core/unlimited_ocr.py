from __future__ import annotations

import atexit
import html
import json
import os
import re
import shutil
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Any

from core.optional_engines import advanced_ocr_runtime_python, advanced_ocr_runtime_ready
from core.paths import PATHS


class UnlimitedOCRError(RuntimeError):
    pass


def narration_text_from_markdown(value: str) -> str:
    """Convert OCR Markdown into conservative narration text."""

    text = html.unescape(str(value or "")).replace("\r\n", "\n")
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    output: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if output and output[-1] != "":
                output.append("")
            continue
        if re.fullmatch(r"\|?[\s:|-]+\|?", line):
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]
            line = ". ".join(cells)
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        line = line.replace("**", "").replace("__", "").replace("`", "")
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            output.append(line)
    return "\n".join(output).strip()


def repetition_problem(text: str) -> str:
    normalized_lines = [
        re.sub(r"\W+", " ", line.casefold()).strip()
        for line in str(text or "").splitlines()
        if line.strip()
    ]
    if len(text) > 120_000:
        return "Advanced OCR output exceeded the safe per-page length."
    counts: dict[str, int] = {}
    for line in normalized_lines:
        if len(line) < 12:
            continue
        counts[line] = counts.get(line, 0) + 1
        if counts[line] >= 5:
            return "Advanced OCR produced a repeated-text loop."
    words = re.findall(r"\w+", str(text or "").casefold())
    if len(words) >= 200:
        for size in (8, 12, 16):
            seen: dict[tuple[str, ...], int] = {}
            for index in range(0, len(words) - size + 1, max(1, size // 2)):
                key = tuple(words[index : index + size])
                seen[key] = seen.get(key, 0) + 1
                if seen[key] >= 8:
                    return "Advanced OCR produced a repeating phrase pattern."
    return ""


class UnlimitedOCRClient:
    """Persistent isolated Unlimited-OCR worker used from the generation thread."""

    def __init__(self) -> None:
        if not advanced_ocr_runtime_ready():
            raise UnlimitedOCRError(
                "Advanced OCR is not installed. Run install_advanced_ocr.ps1 first."
            )
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.RLock()
        self._log_stream = None
        self._device = "Not loaded"
        atexit.register(self.close)

    def _start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        worker = PATHS.project_root / "Scripts" / "advanced_ocr_worker.py"
        python = advanced_ocr_runtime_python()
        if not python.is_file() or not worker.is_file():
            raise UnlimitedOCRError("The Advanced OCR runtime is incomplete.")
        PATHS.logs.mkdir(parents=True, exist_ok=True)
        self._log_stream = (PATHS.logs / "advanced_ocr_worker.log").open(
            "a", encoding="utf-8", buffering=1
        )
        environment = os.environ.copy()
        environment["PYTHONUNBUFFERED"] = "1"
        environment["HF_HOME"] = str(PATHS.models / "HuggingFace")
        environment["TORCH_HOME"] = str(PATHS.models / "Torch")
        environment["AUDIOBOOK_STUDIO_UNLIMITED_OCR_MODEL"] = str(
            PATHS.models / "Unlimited-OCR"
        )
        self._process = subprocess.Popen(
            [str(python), "-u", str(worker)],
            cwd=str(PATHS.project_root),
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._log_stream,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
        )
        while True:
            message = self._read_message()
            message_type = str(message.get("type") or "")
            if message_type == "ready":
                self._device = str(message.get("device") or "CUDA")
                return
            if message_type == "fatal":
                error = str(message.get("error") or "Advanced OCR worker could not start.")
                self.close()
                raise UnlimitedOCRError(error)

    def _read_message(self) -> dict[str, Any]:
        process = self._process
        if process is None or process.stdout is None:
            raise UnlimitedOCRError("Advanced OCR worker is not running.")
        while True:
            line = process.stdout.readline()
            if not line:
                code = process.poll()
                raise UnlimitedOCRError(
                    "Advanced OCR worker stopped unexpectedly"
                    + (f" (exit code {code})." if code is not None else ".")
                )
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value

    def recognize_pixmap(self, pixmap) -> dict[str, Any]:
        with self._lock:
            self._start()
            process = self._process
            if process is None or process.stdin is None:
                raise UnlimitedOCRError("Advanced OCR worker input is unavailable.")
            request_id = uuid.uuid4().hex
            request_root = PATHS.temp / "AdvancedOCR" / request_id
            request_root.mkdir(parents=True, exist_ok=True)
            image_path = request_root / "page.png"
            pixmap.save(image_path)
            try:
                process.stdin.write(
                    json.dumps(
                        {
                            "command": "recognize",
                            "id": request_id,
                            "image_file": str(image_path),
                            "output_dir": str(request_root / "result"),
                        }
                    )
                    + "\n"
                )
                process.stdin.flush()
                while True:
                    response = self._read_message()
                    if str(response.get("id") or "") != request_id:
                        continue
                    if response.get("type") == "status":
                        continue
                    if response.get("type") != "result" or not response.get("ok"):
                        raise UnlimitedOCRError(
                            str(response.get("error") or "Advanced OCR failed.")
                        )
                    text = narration_text_from_markdown(str(response.get("text") or ""))
                    if len(text.split()) < 3:
                        raise UnlimitedOCRError("Advanced OCR did not return enough readable text.")
                    repetition = repetition_problem(text)
                    if repetition:
                        raise UnlimitedOCRError(repetition)
                    return {
                        "text": text,
                        "raw_text": str(response.get("text") or ""),
                        "device": str(response.get("device") or self._device),
                        "model": str(response.get("model") or "baidu/Unlimited-OCR"),
                        "source_file": str(response.get("source_file") or ""),
                    }
            finally:
                shutil.rmtree(request_root, ignore_errors=True)

    def close(self) -> None:
        with self._lock:
            process = self._process
            self._process = None
            if process is not None and process.poll() is None:
                try:
                    if process.stdin is not None:
                        process.stdin.write(
                            json.dumps({"command": "shutdown", "id": "shutdown"}) + "\n"
                        )
                        process.stdin.flush()
                    process.wait(timeout=8)
                except Exception:
                    try:
                        process.terminate()
                        process.wait(timeout=3)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass
            if self._log_stream is not None:
                try:
                    self._log_stream.close()
                except Exception:
                    pass
                self._log_stream = None
