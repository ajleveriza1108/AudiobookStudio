from __future__ import annotations

import json
from pathlib import Path

from core.ocr_layout import OCRRegion, layout_ocr_regions


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "remember_when_structured_regions.json"
PAGE_WIDTH = 1530.0
PAGE_HEIGHT = 1980.0


def _sports_regions() -> list[OCRRegion]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return [OCRRegion(**region) for region in payload["pages"][8]["regions"]]


def test_live_rapidocr_inline_sports_cards_are_split_into_label_and_value():
    original = _sports_regions()
    merged: list[OCRRegion] = []
    index = 0
    source_index = 0
    while index < 18:
        label = original[index]
        value = original[index + 1]
        merged.append(
            OCRRegion(
                text=f"{label.text}: {value.text}",
                left=min(label.left, value.left),
                top=label.top,
                right=max(label.right, value.right),
                bottom=value.bottom,
                confidence=min(label.confidence, value.confidence),
                source_index=source_index,
            )
        )
        source_index += 1
        index += 2
    for region in original[18:]:
        merged.append(
            OCRRegion(
                region.text, region.left, region.top, region.right, region.bottom,
                region.confidence, source_index,
            )
        )
        source_index += 1

    result = layout_ocr_regions(merged, page_width=PAGE_WIDTH, page_height=PAGE_HEIGHT)
    assert result.mode == "sports-cards"
    assert result.details["pairs"] == 9
    assert result.details["inline_pairs"] == 9
    assert "World Series Champion: Detroit Tigers." in result.text
    assert "College Football Champion: Army." in result.text
    assert "Canadian Grey Cup Champion: Toronto Argonauts." in result.text
    assert "Champion Detroit Tigers:" not in result.text


def test_live_rapidocr_fragmented_final_keyword_is_reassembled_before_pairing():
    original = _sports_regions()
    rebuilt: list[OCRRegion] = []
    source_index = 0
    for label, value in zip(original[:18:2], original[1:18:2]):
        words = label.text.split()
        prefix = " ".join(words[:-1])
        keyword = words[-1]
        midpoint = (label.top + label.bottom) / 2.0
        rebuilt.extend(
            [
                OCRRegion(prefix, label.left, label.top, label.right, midpoint, label.confidence, source_index),
                OCRRegion(keyword, label.left, midpoint + 1.0, label.right, label.bottom, label.confidence, source_index + 1),
                OCRRegion(value.text, value.left, value.top, value.right, value.bottom, value.confidence, source_index + 2),
            ]
        )
        source_index += 3
    for region in original[18:]:
        rebuilt.append(
            OCRRegion(
                region.text, region.left, region.top, region.right, region.bottom,
                region.confidence, source_index,
            )
        )
        source_index += 1

    result = layout_ocr_regions(rebuilt, page_width=PAGE_WIDTH, page_height=PAGE_HEIGHT)
    assert result.mode == "sports-cards"
    assert result.details["pairs"] == 9
    assert result.details["fragmented_labels"] == 9
    assert "Indianapolis 500 Winner: The Indianapolis 500 was not held in 1945." in result.text
    assert "Heisman Trophy Winner: Felix Blanchard from Army." in result.text


def test_mixed_live_segmentation_does_not_attach_the_next_label_to_previous_value():
    original = _sports_regions()
    mixed = list(original)
    first_label, first_value = mixed[0], mixed[1]
    mixed[0] = OCRRegion(
        f"{first_label.text} {first_value.text}",
        first_label.left, first_label.top, first_label.right, first_value.bottom,
        first_label.confidence, first_label.source_index,
    )
    del mixed[1]

    result = layout_ocr_regions(mixed, page_width=PAGE_WIDTH, page_height=PAGE_HEIGHT)
    assert result.mode == "sports-cards"
    assert "World Series Champion: Detroit Tigers." in result.text
    assert "Detroit Tigers United States Open Golf Winner" not in result.text
    assert result.text.index("World Series Champion") < result.text.index("United States Open Golf Winner")
