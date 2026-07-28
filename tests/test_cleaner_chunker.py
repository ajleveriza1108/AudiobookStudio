from core.chunker import split_into_chunks, split_sentences
from core.cleaner import clean_text


def test_cleaner_preserves_chapter_and_paragraph_structure():
    raw = """Book Title\n1\n\f\nBook Title\nChapter One\nThis is a para-\ngraph that continues.\n\n\"Hello,\" she said.\n2\n"""
    cleaned = clean_text(raw)

    assert "Chapter One" in cleaned
    assert "paragraph that continues" in cleaned
    assert "\n\n" in cleaned
    assert "\n1\n" not in f"\n{cleaned}\n"


def test_sentence_splitter_protects_common_abbreviations_and_decimals():
    text = "Mr. Jones met Dr. Cruz at 3.50 p.m. They talked. Then they left!"
    sentences = split_sentences(text)

    assert sentences == [
        "Mr. Jones met Dr. Cruz at 3.50 p.m. They talked.",
        "Then they left!",
    ]


def test_chunker_respects_maximum_size():
    text = ("A useful sentence with several words. " * 200).strip()
    chunks = split_into_chunks(text, target_size=300, min_size=120, max_size=420)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert max(map(len, chunks)) <= 420
