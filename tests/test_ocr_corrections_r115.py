from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

from core.ocr_corrections import find_correction_profile
from core.ocr_layout import OCRRegion, layout_ocr_regions, regions_from_tesseract_tsv


def test_tesseract_tsv_quotes_do_not_swallow_following_rows():
    tsv = "\n".join(
        [
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext",
            "5\t1\t1\t1\t1\t1\t10\t10\t60\t20\t96\tI've",
            "5\t1\t1\t1\t1\t2\t75\t10\t50\t20\t95\tSaid",
            "5\t1\t1\t1\t2\t1\t10\t40\t60\t20\t94\tAgain",
        ]
    )
    regions = regions_from_tesseract_tsv(tsv)
    assert [region.text for region in regions] == ["I've Said", "Again"]
    assert all("\t" not in region.text for region in regions)


def test_birth_notice_months_are_not_misclassified_as_timeline():
    regions = [
        OCRRegion("Bette Midler", 30, 100, 180, 125, 0.98, 0),
        OCRRegion("December", 55, 135, 135, 158, 0.98, 1),
        OCRRegion("Van Morrison", 220, 100, 390, 125, 0.98, 2),
        OCRRegion("August", 260, 135, 330, 158, 0.98, 3),
        OCRRegion("Goldie Hawn", 430, 100, 580, 125, 0.98, 4),
        OCRRegion("November", 465, 135, 555, 158, 0.98, 5),
        OCRRegion("January 29", 250, 420, 360, 448, 0.98, 6),
        OCRRegion("February 9", 250, 500, 360, 528, 0.98, 7),
        OCRRegion("March 30", 250, 580, 360, 608, 0.98, 8),
        OCRRegion("June 20", 250, 660, 360, 688, 0.98, 9),
        OCRRegion("October 30", 250, 740, 370, 768, 0.98, 10),
    ]
    result = layout_ocr_regions(regions, page_width=620, page_height=900)
    assert result.mode != "timeline"


def test_profile_loader_matches_exact_content(tmp_path, monkeypatch):
    source = tmp_path / "Remember_When_1945.pdf"
    source.write_bytes(b"verified scanned edition")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    profile_root = tmp_path / "Resources" / "OCRCorrections"
    profile_root.mkdir(parents=True)
    (profile_root / "test.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "id": "test-profile",
                "match": {
                    "sha256": [digest],
                    "size_bytes": source.stat().st_size,
                    "page_count": 10,
                    "filename_contains": ["remember", "1945"],
                },
                "pages": {"1": "Correct page one."},
            }
        ),
        encoding="utf-8",
    )
    import core.ocr_corrections as module

    monkeypatch.setattr(module, "PATHS", SimpleNamespace(project_root=tmp_path))
    profile = find_correction_profile(source, page_count=10)
    assert profile is not None
    assert profile.profile_id == "test-profile"
    assert profile.page_text(1) == "Correct page one."
