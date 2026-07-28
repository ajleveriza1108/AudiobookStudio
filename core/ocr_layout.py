from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from statistics import median
from typing import Any, Iterable, Sequence


MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_MONTH_LOOKUP = {
    "january": 0,
    "jan": 0,
    "february": 1,
    "feb": 1,
    "march": 2,
    "mar": 2,
    "april": 3,
    "apr": 3,
    "may": 4,
    "june": 5,
    "jun": 5,
    "july": 6,
    "jul": 6,
    "august": 7,
    "aug": 7,
    "september": 8,
    "sept": 8,
    "sep": 8,
    "october": 9,
    "oct": 9,
    "november": 10,
    "nov": 10,
    "december": 11,
    "dec": 11,
}


@dataclass(frozen=True)
class OCRRegion:
    text: str
    left: float
    top: float
    right: float
    bottom: float
    confidence: float = 1.0
    source_index: int = 0

    @property
    def width(self) -> float:
        return max(0.0, self.right - self.left)

    @property
    def height(self) -> float:
        return max(0.0, self.bottom - self.top)

    @property
    def center_x(self) -> float:
        return (self.left + self.right) / 2.0

    @property
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OCRLayoutResult:
    text: str
    mode: str
    confidence: float
    regions: tuple[OCRRegion, ...]
    reading_order: tuple[int, ...]
    warnings: tuple[str, ...] = ()
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "confidence": round(float(self.confidence), 4),
            "text": self.text,
            "reading_order": list(self.reading_order),
            "warnings": list(self.warnings),
            "details": dict(self.details or {}),
            "regions": [region.to_dict() for region in self.regions],
        }


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _box_bounds(box: Any) -> tuple[float, float, float, float] | None:
    if box is None:
        return None
    try:
        values = box.tolist() if hasattr(box, "tolist") else box
    except Exception:
        values = box

    if isinstance(values, dict):
        left = values.get("left", values.get("x", values.get("x0")))
        top = values.get("top", values.get("y", values.get("y0")))
        right = values.get("right", values.get("x1"))
        bottom = values.get("bottom", values.get("y1"))
        width = values.get("width", values.get("w"))
        height = values.get("height", values.get("h"))
        if right is None and left is not None and width is not None:
            right = _safe_float(left) + _safe_float(width)
        if bottom is None and top is not None and height is not None:
            bottom = _safe_float(top) + _safe_float(height)
        if None not in (left, top, right, bottom):
            return (
                _safe_float(left),
                _safe_float(top),
                _safe_float(right),
                _safe_float(bottom),
            )
        return None

    if isinstance(values, (list, tuple)):
        # [left, top, right, bottom]
        if len(values) == 4 and all(not isinstance(item, (list, tuple)) for item in values):
            left, top, right, bottom = (_safe_float(item) for item in values)
            return left, top, right, bottom

        points: list[tuple[float, float]] = []
        for item in values:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                points.append((_safe_float(item[0]), _safe_float(item[1])))
        if points:
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return min(xs), min(ys), max(xs), max(ys)
    return None


def _normalize_confidence(value: Any) -> float:
    confidence = _safe_float(value, 1.0)
    if confidence > 1.0:
        confidence /= 100.0
    return max(0.0, min(1.0, confidence))


def regions_from_rapidocr(result: Any, *, min_confidence: float = 0.30) -> list[OCRRegion]:
    """Convert RapidOCR 1.x/2.x/3.x outputs into coordinate-preserving regions."""

    if result is None:
        return []

    boxes = getattr(result, "boxes", None)
    texts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    if boxes is not None and texts is not None:
        scores = scores if scores is not None else [1.0] * len(texts)
        output: list[OCRRegion] = []
        for index, (box, text, score) in enumerate(zip(boxes, texts, scores)):
            text = str(text or "").strip()
            bounds = _box_bounds(box)
            confidence = _normalize_confidence(score)
            if text and bounds and confidence >= min_confidence:
                output.append(OCRRegion(text, *bounds, confidence, index))
        return output

    if isinstance(result, dict):
        def first_present(*names: str):
            for name in names:
                value = result.get(name)
                if value is not None:
                    return value
            return None

        boxes = first_present("boxes", "dt_boxes", "polygons")
        texts = first_present("txts", "texts")
        scores = first_present("scores", "confs", "confidence")
        if boxes is not None and texts is not None:
            scores = scores if isinstance(scores, (list, tuple)) else [1.0] * len(texts)
            output = []
            for index, (box, text, score) in enumerate(zip(boxes, texts, scores)):
                text = str(text or "").strip()
                bounds = _box_bounds(box)
                confidence = _normalize_confidence(score)
                if text and bounds and confidence >= min_confidence:
                    output.append(OCRRegion(text, *bounds, confidence, index))
            return output

    # RapidOCR 1.x often returned (result_list, elapsed).
    if isinstance(result, tuple) and result:
        first = result[0]
        if isinstance(first, (list, tuple)):
            result = first

    output: list[OCRRegion] = []
    if isinstance(result, (list, tuple)):
        for index, item in enumerate(result):
            if isinstance(item, dict):
                text = item.get("text") or item.get("txt")
                box = item.get("box") or item.get("points") or item.get("polygon")
                score = item.get("score", item.get("confidence", 1.0))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                box, text = item[0], item[1]
                score = item[2] if len(item) >= 3 else 1.0
            else:
                continue
            text = str(text or "").strip()
            bounds = _box_bounds(box)
            confidence = _normalize_confidence(score)
            if text and bounds and confidence >= min_confidence:
                output.append(OCRRegion(text, *bounds, confidence, index))
    return output


def regions_from_tesseract_tsv(tsv_text: str, *, min_confidence: float = 0.30) -> list[OCRRegion]:
    """Group Tesseract TSV words into line regions with bounding boxes.

    Tesseract's TSV is not RFC CSV. OCR text can contain quotes, so using
    csv.DictReader can accidentally merge the remaining TSV rows into one text
    field. Parse each physical line by tabs instead.
    """

    physical_lines = str(tsv_text or "").splitlines()
    if not physical_lines:
        return []
    headers = physical_lines[0].split("\t")
    index = {name: position for position, name in enumerate(headers)}
    required = {"level", "page_num", "block_num", "par_num", "line_num", "word_num", "left", "top", "width", "height", "conf", "text"}
    if not required.issubset(index):
        return []

    lines: dict[tuple[int, int, int, int], list[dict[str, Any]]] = {}
    for physical in physical_lines[1:]:
        columns = physical.split("\t")
        if len(columns) < len(headers):
            columns.extend([""] * (len(headers) - len(columns)))
        elif len(columns) > len(headers):
            # Preserve literal tabs recognized inside the final text field.
            columns = columns[: len(headers) - 1] + [" ".join(columns[len(headers) - 1 :])]

        def field(name: str) -> str:
            position = index[name]
            return columns[position] if position < len(columns) else ""

        try:
            if int(field("level") or 0) != 5:
                continue
        except ValueError:
            continue
        text = field("text").strip()
        confidence = _normalize_confidence(field("conf"))
        if not text or confidence < 0.05:
            continue
        try:
            key = (
                int(field("page_num") or 1),
                int(field("block_num") or 0),
                int(field("par_num") or 0),
                int(field("line_num") or 0),
            )
            word_num = int(field("word_num") or 0)
        except ValueError:
            continue
        lines.setdefault(key, []).append(
            {
                "text": text,
                "left": _safe_float(field("left")),
                "top": _safe_float(field("top")),
                "width": _safe_float(field("width")),
                "height": _safe_float(field("height")),
                "confidence": confidence,
                "word_num": word_num,
            }
        )

    output: list[OCRRegion] = []
    for index, words in enumerate(lines.values()):
        words.sort(key=lambda item: (item["word_num"], item["left"]))
        text = " ".join(item["text"] for item in words).strip()
        left = min(item["left"] for item in words)
        top = min(item["top"] for item in words)
        right = max(item["left"] + item["width"] for item in words)
        bottom = max(item["top"] + item["height"] for item in words)
        confidence = sum(item["confidence"] for item in words) / max(1, len(words))
        if confidence >= min_confidence or max(item["confidence"] for item in words) >= 0.70:
            output.append(OCRRegion(text, left, top, right, bottom, confidence, index))
    return output


def _normalize_anchor(text: str) -> str:
    return re.sub(r"[^a-z]", "", str(text or "").casefold())


def _month_index(text: str) -> int | None:
    normalized = _normalize_anchor(text)
    return _MONTH_LOOKUP.get(normalized)


def _is_decorative(region: OCRRegion, page_width: float, page_height: float) -> bool:
    text = str(region.text or "").strip()
    if not text:
        return True
    if not any(character.isalnum() for character in text):
        return True
    narrow = region.width <= max(5.0, page_width * 0.012)
    tall = region.height >= max(12.0, region.width * 3.0)
    if narrow and tall and _normalize_anchor(text) in {"i", "l", "one"}:
        return True
    return False


def _join_regions(regions: Iterable[OCRRegion]) -> str:
    ordered = sorted(regions, key=lambda item: (round(item.top, 1), item.left, item.source_index))
    pieces: list[str] = []
    for region in ordered:
        text = re.sub(r"\s+", " ", region.text).strip()
        if not text:
            continue
        if pieces and pieces[-1].endswith("-") and text[:1].islower():
            pieces[-1] = pieces[-1][:-1] + text
        else:
            pieces.append(text)
    joined = " ".join(pieces)
    joined = re.sub(r"\s+([,.;:!?])", r"\1", joined)
    return re.sub(r"\s+", " ", joined).strip()


def _cluster_by_y(regions: Sequence[OCRRegion], tolerance: float) -> list[list[OCRRegion]]:
    clusters: list[list[OCRRegion]] = []
    for region in sorted(regions, key=lambda item: (item.center_y, item.center_x)):
        target: list[OCRRegion] | None = None
        best_distance = math.inf
        for cluster in clusters:
            center = median(item.center_y for item in cluster)
            distance = abs(region.center_y - center)
            if distance <= tolerance and distance < best_distance:
                target = cluster
                best_distance = distance
        if target is None:
            clusters.append([region])
        else:
            target.append(region)
    return sorted(clusters, key=lambda cluster: median(item.center_y for item in cluster))


def _timeline_layout(
    regions: Sequence[OCRRegion], page_width: float, page_height: float
) -> OCRLayoutResult | None:
    anchors_by_month: dict[int, OCRRegion] = {}
    for region in regions:
        month = _month_index(region.text)
        if month is None:
            continue
        previous = anchors_by_month.get(month)
        if previous is None or region.confidence > previous.confidence:
            anchors_by_month[month] = region

    anchors = list(anchors_by_month.values())
    if len(anchors) < 4:
        return None

    anchor_heights = [max(1.0, item.height) for item in anchors]
    row_tolerance = max(page_height * 0.035, median(anchor_heights) * 1.9)
    rows = _cluster_by_y(anchors, row_tolerance)
    rows = [sorted(row, key=lambda item: item.center_x) for row in rows]
    multi_anchor_rows = sum(1 for row in rows if len(row) >= 2)
    if len(rows) < 2 or max(len(row) for row in rows) < 2 or multi_anchor_rows < 2:
        return None

    # A timeline/calendar should contain a meaningful run of canonical month anchors.
    month_numbers = sorted(anchors_by_month)
    consecutive = sum(1 for a, b in zip(month_numbers, month_numbers[1:]) if b == a + 1)
    if consecutive < max(2, len(month_numbers) // 2):
        return None

    row_centers = [median(item.center_y for item in row) for row in rows]
    row_tops = [min(item.top for item in row) for row in rows]
    first_anchor_top = min(item.top for item in anchors)
    grid_top = max(0.0, first_anchor_top - page_height * 0.025)

    assignments: dict[int, list[OCRRegion]] = {month: [] for month in anchors_by_month}
    anchor_ids = {id(item) for item in anchors}
    intro: list[OCRRegion] = []
    outro: list[OCRRegion] = []

    for region in regions:
        if id(region) in anchor_ids or _is_decorative(region, page_width, page_height):
            continue
        if region.center_y < grid_top:
            intro.append(region)
            continue

        assigned = False
        for row_index, row in enumerate(rows):
            current_center = row_centers[row_index]
            top_bound = (
                grid_top
                if row_index == 0
                else row_tops[row_index] - page_height * 0.018
            )
            bottom_bound = (
                page_height
                if row_index == len(rows) - 1
                else row_tops[row_index + 1] - page_height * 0.018
            )
            if not (top_bound <= region.center_y < bottom_bound):
                continue

            centers = [item.center_x for item in row]
            for column_index, anchor in enumerate(row):
                left_bound = 0.0 if column_index == 0 else (centers[column_index - 1] + centers[column_index]) / 2.0
                right_bound = (
                    page_width
                    if column_index == len(row) - 1
                    else (centers[column_index] + centers[column_index + 1]) / 2.0
                )
                # Descriptions on this design sit below their month heading. Avoid
                # pulling a page title or running header into the first cell.
                minimum_body_y = anchor.bottom - max(2.0, anchor.height * 0.15)
                if (
                    left_bound <= region.center_x < right_bound
                    and region.center_y >= minimum_body_y
                ):
                    month = _month_index(anchor.text)
                    if month is not None:
                        assignments[month].append(region)
                        assigned = True
                    break
            if assigned:
                break

        if not assigned and region.center_y >= row_centers[-1]:
            outro.append(region)

    paragraphs: list[str] = []
    reading_order: list[int] = []
    intro_text = _join_regions(intro)
    if intro_text:
        paragraphs.append(intro_text)
        reading_order.extend(item.source_index for item in sorted(intro, key=lambda item: (item.top, item.left)))

    populated = 0
    for month in sorted(anchors_by_month):
        body = assignments.get(month, [])
        body_text = _join_regions(body)
        anchor = anchors_by_month[month]
        if body_text:
            populated += 1
            paragraphs.append(f"{MONTHS[month]}: {body_text}")
        else:
            paragraphs.append(f"{MONTHS[month]}.")
        reading_order.append(anchor.source_index)
        reading_order.extend(item.source_index for item in sorted(body, key=lambda item: (item.top, item.left)))

    outro_text = _join_regions(outro)
    if outro_text:
        paragraphs.append(outro_text)
        reading_order.extend(item.source_index for item in sorted(outro, key=lambda item: (item.top, item.left)))

    anchor_ratio = min(1.0, len(anchors_by_month) / 9.0)
    body_ratio = populated / max(1, len(anchors_by_month))
    confidence = min(0.99, 0.72 + 0.17 * anchor_ratio + 0.10 * body_ratio)
    warnings: list[str] = []
    if populated < len(anchors_by_month):
        warnings.append("One or more month cells had no recognized description text.")

    return OCRLayoutResult(
        text="\n\n".join(paragraphs).strip(),
        mode="timeline",
        confidence=confidence,
        regions=tuple(regions),
        reading_order=tuple(reading_order),
        warnings=tuple(warnings),
        details={
            "anchors": {MONTHS[index]: anchors_by_month[index].to_dict() for index in sorted(anchors_by_month)},
            "rows": len(rows),
            "months_detected": [MONTHS[index] for index in sorted(anchors_by_month)],
            "populated_cells": populated,
        },
    )


def _vertical_gap_split(regions: Sequence[OCRRegion], page_width: float) -> list[list[OCRRegion]] | None:
    candidates = [region for region in regions if region.width < page_width * 0.72]
    if len(candidates) < 6:
        return None
    sorted_regions = sorted(candidates, key=lambda item: item.left)
    gaps: list[tuple[float, float]] = []
    running_right = sorted_regions[0].right
    for current in sorted_regions[1:]:
        gap = current.left - running_right
        if gap > page_width * 0.055:
            gaps.append((gap, (current.left + running_right) / 2.0))
        running_right = max(running_right, current.right)
    if not gaps:
        return None

    split_points = [point for _, point in sorted(gaps, reverse=True)[:3]]
    split_points.sort()
    columns: list[list[OCRRegion]] = [[] for _ in range(len(split_points) + 1)]
    for region in regions:
        column_index = sum(1 for point in split_points if region.center_x >= point)
        columns[column_index].append(region)
    columns = [column for column in columns if len(column) >= 2]
    if len(columns) < 2:
        return None

    centers = [median(item.center_x for item in column) for column in columns]
    if any((right - left) < page_width * 0.14 for left, right in zip(centers, centers[1:])):
        return None
    return sorted(columns, key=lambda column: median(item.center_x for item in column))


def _generic_layout(regions: Sequence[OCRRegion], page_width: float, page_height: float) -> OCRLayoutResult:
    visible = [region for region in regions if not _is_decorative(region, page_width, page_height)]
    if not visible:
        return OCRLayoutResult("", "empty", 0.0, tuple(regions), tuple(), ("No readable OCR regions were found.",), {})

    columns = _vertical_gap_split(visible, page_width)
    if columns:
        paragraphs: list[str] = []
        order: list[int] = []
        for column in columns:
            text = _join_regions(column)
            if text:
                paragraphs.append(text)
            order.extend(item.source_index for item in sorted(column, key=lambda item: (item.top, item.left)))
        return OCRLayoutResult(
            text="\n\n".join(paragraphs).strip(),
            mode="multi-column",
            confidence=0.78,
            regions=tuple(regions),
            reading_order=tuple(order),
            warnings=("Multiple text columns were detected and ordered column by column.",),
            details={"columns": len(columns)},
        )

    ordered = sorted(visible, key=lambda item: (item.top, item.left, item.source_index))
    return OCRLayoutResult(
        text=_join_regions(ordered),
        mode="standard",
        confidence=0.90,
        regions=tuple(regions),
        reading_order=tuple(item.source_index for item in ordered),
        warnings=(),
        details={"columns": 1},
    )


def layout_ocr_regions(
    regions: Sequence[OCRRegion],
    *,
    page_width: float,
    page_height: float,
) -> OCRLayoutResult:
    """Create narration text from OCR regions without flattening unrelated cells."""

    clean_regions = [
        OCRRegion(
            re.sub(r"\s+", " ", str(region.text or "")).strip(),
            max(0.0, float(region.left)),
            max(0.0, float(region.top)),
            max(0.0, float(region.right)),
            max(0.0, float(region.bottom)),
            max(0.0, min(1.0, float(region.confidence))),
            int(region.source_index),
        )
        for region in regions
        if str(region.text or "").strip()
    ]
    timeline = _timeline_layout(clean_regions, float(page_width), float(page_height))
    if timeline is not None:
        return timeline
    return _generic_layout(clean_regions, float(page_width), float(page_height))
