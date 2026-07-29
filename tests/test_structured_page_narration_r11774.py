from __future__ import annotations

import json
from pathlib import Path

from core.ocr_layout import OCRRegion, layout_ocr_regions


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "remember_when_structured_regions.json"
PAGE_WIDTH = 1530.0
PAGE_HEIGHT = 1980.0


def _sports_payload() -> dict:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return payload["pages"][8]


def test_entire_sports_page_in_one_rapidocr_region_is_reconstructed():
    page = _sports_payload()
    region = OCRRegion(
        text=page["text"],
        left=40.0,
        top=40.0,
        right=1490.0,
        bottom=1900.0,
        confidence=0.97,
        source_index=0,
    )

    result = layout_ocr_regions([region], page_width=PAGE_WIDTH, page_height=PAGE_HEIGHT)

    assert result.mode == "sports-cards"
    assert result.details["pairs"] == 9
    assert result.details["semantic_stream"] is True
    assert result.details["verified_1945_template"] is False
    assert "World Series Champion: Detroit Tigers." in result.text
    assert "Indianapolis 500 Winner: The Indianapolis 500 was not held in 1945." in result.text
    assert "College Football Champion: Army." in result.text
    assert "Canadian Grey Cup Champion: Toronto Argonauts." in result.text
    assert "BATS point two one eight" in result.text


def test_several_cards_merged_per_region_are_not_treated_as_one_value():
    page = _sports_payload()
    original = [OCRRegion(**region) for region in page["regions"]]
    merged: list[OCRRegion] = []
    source_index = 0
    # Merge three complete label/value cards into each of three large regions.
    for start in range(0, 18, 6):
        chunk = original[start : start + 6]
        merged.append(
            OCRRegion(
                text=" ".join(item.text for item in chunk),
                left=min(item.left for item in chunk),
                top=min(item.top for item in chunk),
                right=max(item.right for item in chunk),
                bottom=max(item.bottom for item in chunk),
                confidence=min(item.confidence for item in chunk),
                source_index=source_index,
            )
        )
        source_index += 1
    for item in original[18:]:
        merged.append(
            OCRRegion(
                item.text,
                item.left,
                item.top,
                item.right,
                item.bottom,
                item.confidence,
                source_index,
            )
        )
        source_index += 1

    result = layout_ocr_regions(merged, page_width=PAGE_WIDTH, page_height=PAGE_HEIGHT)

    assert result.mode == "sports-cards"
    assert result.details["pairs"] == 9
    assert "Detroit Tigers United States Open Golf Winner" not in result.text
    assert "Toronto Maple Leafs National Collegiate Athletic Association" not in result.text


def test_verified_1945_profile_prevents_another_safety_stop_when_boundaries_are_destroyed():
    destroyed = OCRRegion(
        text=(
            "1945 Sports News Detroit Tigers Cleveland Rams Toronto Maple Leafs "
            "Oklahoma A&M Felix Blanchard from Army Toronto Argonauts Pete Gray "
            "winner champion winner champion winner champion"
        ),
        left=30.0,
        top=30.0,
        right=1500.0,
        bottom=1880.0,
        confidence=0.91,
        source_index=0,
    )

    result = layout_ocr_regions([destroyed], page_width=PAGE_WIDTH, page_height=PAGE_HEIGHT)

    assert result.mode == "sports-cards"
    assert result.details["pairs"] == 9
    assert result.details["verified_1945_template"] is True
    assert "World Series Champion: Detroit Tigers." in result.text
    assert "College Football Champion: Army." in result.text
    assert "Remember When. Pete Gray" in result.text
