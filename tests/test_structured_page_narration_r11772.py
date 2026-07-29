from __future__ import annotations

import json
from pathlib import Path

from core.ocr import OCRService
from core.ocr_layout import OCRRegion, layout_ocr_regions
from core.ocr_structured import structured_layout_requirement


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "remember_when_structured_regions.json"
PAGE_WIDTH = 1530.0
PAGE_HEIGHT = 1980.0


def _pages():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return payload["pages"]


def _layout(page_number: int):
    page = _pages()[page_number - 1]
    regions = tuple(OCRRegion(**region) for region in page["regions"])
    return layout_ocr_regions(
        regions,
        page_width=PAGE_WIDTH,
        page_height=PAGE_HEIGHT,
    )


def test_r11772_version_and_cache_contract():
    version = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    assert "R1.17.7.5" in version
    assert "BUILD = 1775" in version
    assert OCRService.CACHE_SCHEMA == 9
    assert OCRService.LAYOUT_SCHEMA == 8


def test_cover_discards_decorative_product_artifacts():
    result = _layout(1)
    assert result.mode == "cover-title"
    assert "NOSTALGIC LOOK BACK IN TIME" in result.text.upper()
    for artifact in ("TV", "DINNER", "GAS", "LINCOLN", "IKE"):
        assert artifact not in result.text.upper()


def test_inline_dedication_fields_are_separated_and_ordered():
    regions = (
        OCRRegion("Remember When, 1945", 300, 250, 1200, 360, 0.98, 0),
        OCRRegion("To", 280, 700, 340, 750, 0.99, 1),
        OCRRegion("Dad", 470, 690, 610, 755, 0.98, 2),
        OCRRegion("From: Dan+ Diana", 280, 850, 800, 915, 0.98, 3),
        OCRRegion("Date: 8-7-26", 280, 990, 800, 1060, 0.98, 4),
        OCRRegion(
            "The richness of life lies in the memories we have forgotten.",
            400,
            1350,
            1150,
            1550,
            0.98,
            5,
        ),
    )
    result = layout_ocr_regions(regions, page_width=1530, page_height=1980)
    assert result.mode == "form-fields-v2"
    assert result.text.index("To Dad.") < result.text.index("From Dan and Diana.")
    assert result.text.index("From Dan and Diana.") < result.text.index("Date: August 7, 2026.")
    assert "Dad From" not in result.text


def test_timeline_keeps_month_sequence_and_removes_running_footer():
    result = _layout(3)
    assert result.mode == "timeline"
    positions = [result.text.index(f"{month}:") for month in ("January", "February", "March", "December")]
    assert positions == sorted(positions)
    assert "SeekPublishing" not in result.text
    assert "top Dodgers farm team. Remember When" not in result.text
    assert result.text.rstrip().endswith("The microwave oven is patented.")


def test_world_news_follows_timeline_without_footer_noise():
    timeline = _layout(3).text
    world_news = _layout(4).text
    joined = timeline + "\n\n" + world_news
    assert joined.index("The microwave oven is patented.") < joined.index("World News")
    assert "SeekPublishing" not in joined


def test_interesting_facts_pairs_each_label_with_its_value():
    result = _layout(6)
    assert result.mode == "fact-cards"
    expected = (
        "President of the United States: Franklin Roosevelt, then Harry Truman.",
        "Vice President of the United States: Harry Truman, then None.",
        "Pulitzer Prize Winner: A Bell for Adano by John Hersey.",
        "Nobel Peace Prize Winner: Cordell Hull.",
        "Life Expectancy: 62.9 Years.",
    )
    for phrase in expected:
        assert phrase in result.text
    assert result.text.index(expected[0]) < result.text.index(expected[1])
    assert "Vice President of President" not in result.text


def test_cost_of_living_reads_item_before_price():
    result = _layout(7)
    assert result.mode == "key-value-table"
    for phrase in (
        "New House: $4,625.00.",
        "Average Income: $2,390.00 per year.",
        "Bacon: 45¢ per pound.",
        "Eggs: 22¢ per dozen.",
        "Fresh Baked Bread: 9¢ per loaf.",
    ):
        assert phrase in result.text
    assert "$4,625.00 New House" not in result.text
    assert "Bacon Eggs" not in result.text


def test_birth_notices_read_one_complete_column_at_a_time():
    result = _layout(8)
    assert result.mode == "profile-columns"
    b = result.text.index("Bette Midler.")
    v = result.text.index("Sir Van Morrison.")
    g = result.text.index("Goldie Hawn.")
    assert b < v < g
    assert result.text.index("December 1.", b) < v
    assert result.text.index("August 31.", v) < g
    assert "Bette Midler Sir Van Morrison Goldie Hawn" not in result.text
    assert "December 1 August 31 November 21" not in result.text
    assert "January 29: Tom Selleck (Actor)." in result.text
    assert "October 30: Henry Winkler (Actor)." in result.text


def test_sports_cards_pair_labels_and_values_and_normalize_batting_average():
    result = _layout(9)
    assert result.mode == "sports-cards"
    assert "World Series Champion: Detroit Tigers." in result.text
    assert "College Football Champion: Army." in result.text
    assert "BATS point two one eight" in result.text
    assert "SeekPublishing" not in result.text


def test_music_and_movies_are_separate_lists_with_ocr_word_repair():
    result = _layout(10)
    assert result.mode == "music-movie-lists"
    assert "Accentuate the Positive - by Johnny Mercer." in result.text
    assert "The Lost Weekend, Academy Award Winner." in result.text
    assert "And Then There Were None." in result.text
    assert "Ac-Cent--Tachu-Ate" not in result.text
    assert "SeekPublishing" not in result.text


def test_structured_pages_are_not_allowed_to_fall_back_to_flattened_text():
    requirements = {
        "1945 COST OF LIVING LIVING New House $4,625": "key-value-table",
        "1945 BIRTH NOTICES Bette Midler Sir Van Morrison Goldie Hawn": "profile-columns",
        "1945 INTERESTING FACTS Pulitzer Prize Winner Life Expectancy": "fact-cards",
        "1945 MUSIC & MOVIE FAVORITES Music Movies": "music-movie-lists",
        "World Series Champion U.S. Open Golf Winner Pro Football Champion Indianapolis 500 Winner Stanley Cup Winner NCAA Basketball Champion": "sports-cards",
    }
    for text, expected_mode in requirements.items():
        requirement = structured_layout_requirement(text)
        assert requirement is not None
        assert expected_mode in requirement[1]
