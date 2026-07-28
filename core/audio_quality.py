from __future__ import annotations

from array import array
import json
import math
import os
from pathlib import Path
import wave
from typing import Any


class AudioQualityAnalyzer:
    """Creates a lightweight narration-quality report from PCM WAV audio."""

    @staticmethod
    def analyze(file: str | Path, sample_limit: int = 2_000_000) -> dict[str, Any]:
        path = Path(file)
        result: dict[str, Any] = {
            "file": str(path),
            "valid": False,
            "duration_seconds": 0.0,
            "sample_rate": 0,
            "channels": 0,
            "sample_width": 0,
            "peak_dbfs": None,
            "rms_dbfs": None,
            "clipped_percent": 0.0,
            "near_silence_percent": 0.0,
            "warnings": [],
        }

        if not path.is_file():
            result["warnings"].append("The final WAV file was not found.")
            return result

        try:
            with wave.open(str(path), "rb") as audio:
                channels = audio.getnchannels()
                sample_width = audio.getsampwidth()
                sample_rate = audio.getframerate()
                frames = audio.getnframes()
                result.update(
                    {
                        "duration_seconds": frames / sample_rate if sample_rate else 0.0,
                        "sample_rate": sample_rate,
                        "channels": channels,
                        "sample_width": sample_width,
                    }
                )

                if sample_width != 2:
                    result["warnings"].append(
                        "Detailed peak analysis is available only for 16-bit PCM WAV audio."
                    )
                    result["valid"] = frames > 0 and sample_rate > 0 and channels > 0
                    return result

                stride = max(1, frames // max(1, sample_limit // max(1, channels)))
                peak = 0
                square_sum = 0.0
                sample_count = 0
                clipped = 0
                near_silence = 0
                frame_index = 0

                while True:
                    raw = audio.readframes(65536)
                    if not raw:
                        break
                    values = array("h")
                    values.frombytes(raw)
                    if os.sys.byteorder != "little":
                        values.byteswap()
                    for offset in range(0, len(values), stride * max(1, channels)):
                        value = int(values[offset])
                        magnitude = abs(value)
                        peak = max(peak, magnitude)
                        square_sum += float(value * value)
                        sample_count += 1
                        if magnitude >= 32760:
                            clipped += 1
                        if magnitude <= 96:
                            near_silence += 1
                    frame_index += len(values) // max(1, channels)

                if sample_count:
                    full_scale = 32768.0
                    rms = math.sqrt(square_sum / sample_count)
                    result["peak_dbfs"] = round(20 * math.log10(max(peak, 1) / full_scale), 2)
                    result["rms_dbfs"] = round(20 * math.log10(max(rms, 1) / full_scale), 2)
                    result["clipped_percent"] = round((clipped / sample_count) * 100, 4)
                    result["near_silence_percent"] = round((near_silence / sample_count) * 100, 2)

                result["valid"] = frames > 0 and sample_rate > 0 and channels > 0
        except (OSError, wave.Error) as error:
            result["warnings"].append(f"The WAV file could not be analyzed: {error}")
            return result

        peak_dbfs = result.get("peak_dbfs")
        rms_dbfs = result.get("rms_dbfs")
        if result["clipped_percent"] > 0.01:
            result["warnings"].append("Possible clipping was detected in the final narration.")
        if isinstance(peak_dbfs, (int, float)) and peak_dbfs > -0.5:
            result["warnings"].append("The audio peak is very close to full scale.")
        if isinstance(rms_dbfs, (int, float)) and rms_dbfs < -35:
            result["warnings"].append("The average narration level may be unusually quiet.")
        if result["near_silence_percent"] > 70:
            result["warnings"].append("A large portion of the sampled audio is near silence.")

        return result

    @staticmethod
    def save(report: dict[str, Any], folder: str | Path) -> tuple[Path, Path]:
        root = Path(folder)
        root.mkdir(parents=True, exist_ok=True)
        json_path = root / "audio_quality_report.json"
        text_path = root / "Audio Quality Report.txt"

        temporary = json_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, json_path)

        lines = [
            "AUDIOBOOK STUDIO - AUDIO QUALITY REPORT",
            "=" * 70,
            f"File: {report.get('file', '')}",
            f"Duration: {float(report.get('duration_seconds', 0.0)):.1f} seconds",
            f"Format: {report.get('sample_rate', 0)} Hz, {report.get('channels', 0)} channel(s), {int(report.get('sample_width', 0)) * 8}-bit",
            f"Peak: {report.get('peak_dbfs')} dBFS",
            f"Average level: {report.get('rms_dbfs')} dBFS",
            f"Possible clipped samples: {report.get('clipped_percent', 0.0)}%",
            f"Near-silence samples: {report.get('near_silence_percent', 0.0)}%",
            "",
        ]
        warnings = list(report.get("warnings", []))
        if warnings:
            lines.append("Review items:")
            lines.extend(f"- {warning}" for warning in warnings)
        else:
            lines.append("No obvious structural audio warnings were detected.")
        lines.append("")
        lines.append("Listen to several chapter beginnings, endings, names, and regenerated sections before distribution.")
        text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return json_path, text_path
