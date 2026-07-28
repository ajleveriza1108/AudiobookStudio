from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from core.ocr import OCRService
from core.ocr_layout import OCRRegion, layout_ocr_regions, regions_from_rapidocr


def _region(text: str, left: float, top: float, right: float, bottom: float, index: int) -> OCRRegion:
    return OCRRegion(text, left, top, right, bottom, 0.95, index)


def test_timeline_cells_are_narrated_month_by_month_not_across_rows():
    regions = [
        _region("January", 120, 50, 210, 80, 0),
        _region("February", 320, 50, 430, 80, 1),
        _region("March", 550, 50, 625, 80, 2),
        _region("Pepe LePew debuts in", 70, 155, 265, 176, 3),
        _region("the Warner Bros cartoon", 70, 180, 270, 200, 4),
        _region("Odor-able Kitty.", 100, 205, 240, 225, 5),
        _region("Walt Disney's", 315, 155, 440, 176, 6),
        _region("The 3 Caballeros", 305, 180, 455, 200, 7),
        _region("opens in New York.", 300, 205, 465, 225, 8),
        _region("Phyllis M. Daley", 515, 155, 665, 176, 9),
        _region("is the first black nurse", 505, 180, 675, 200, 10),
        _region("sworn-in as a U.S. Navy ensign.", 500, 205, 690, 230, 11),
        _region("April", 145, 265, 205, 290, 12),
        _region("May", 355, 265, 400, 290, 13),
        _region("June", 560, 265, 610, 290, 14),
        _region("The NFL requires players", 90, 370, 250, 390, 15),
        _region("to wear long stockings.", 100, 395, 240, 415, 16),
        _region("Arthur C. Clarke proposes", 295, 370, 480, 390, 17),
        _region("relay satellites in geosynchronous orbit.", 285, 395, 490, 420, 18),
        _region("The Charter of the United Nations", 510, 370, 680, 395, 19),
        _region("is signed.", 550, 400, 630, 420, 20),
    ]

    result = layout_ocr_regions(regions, page_width=737, page_height=763)

    assert result.mode == "timeline"
    assert "January: Pepe LePew debuts in the Warner Bros cartoon Odor-able Kitty." in result.text
    assert "February: Walt Disney's The 3 Caballeros opens in New York." in result.text
    assert "March: Phyllis M. Daley is the first black nurse sworn-in as a U.S. Navy ensign." in result.text
    assert "Pepe LePew debuts in Walt Disney's Phyllis M. Daley" not in result.text
    assert result.text.index("January:") < result.text.index("February:") < result.text.index("March:")
    assert result.text.index("April:") < result.text.index("May:") < result.text.index("June:")


def test_rapidocr_3_result_preserves_boxes_and_scores():
    result = SimpleNamespace(
        boxes=[[[10, 20], [90, 20], [90, 40], [10, 40]]],
        txts=["January"],
        scores=[0.98],
    )
    regions = regions_from_rapidocr(result)
    assert len(regions) == 1
    assert regions[0].text == "January"
    assert regions[0].left == 10
    assert regions[0].bottom == 40
    assert regions[0].confidence == 0.98


def test_pre_layout_cache_is_rejected(tmp_path, monkeypatch):
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-layout-cache-test")
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "ocr_text.txt").write_text("wrong old row flattened text", encoding="utf-8")
    (cache / "manifest.json").write_text(
        json.dumps({"schema": 1, "backend": "RapidOCR", "pages": 1}),
        encoding="utf-8",
    )
    monkeypatch.setattr(OCRService, "cache_folder", classmethod(lambda cls, path: cache))
    assert OCRService.cached_text(source) is None


def test_layout_cache_schema_is_accepted(tmp_path, monkeypatch):
    source = tmp_path / "scan.pdf"
    source.write_bytes(b"%PDF-layout-cache-test-new")
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "ocr_text.txt").write_text(
        "January: A correct timeline entry with enough readable words.", encoding="utf-8"
    )
    (cache / "manifest.json").write_text(
        json.dumps(
            {
                "schema": OCRService.CACHE_SCHEMA,
                "layout_schema": OCRService.LAYOUT_SCHEMA,
                "backend": "RapidOCR",
                "pages": 1,
                "ocr_pages": 1,
                "structured_pages": 1,
                "timeline_pages": 1,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(OCRService, "cache_folder", classmethod(lambda cls, path: cache))
    result = OCRService.cached_text(source)
    assert result is not None
    assert result.timeline_pages == 1
    assert result.layout_schema == OCRService.LAYOUT_SCHEMA
