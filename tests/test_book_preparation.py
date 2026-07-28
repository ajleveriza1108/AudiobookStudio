from core.book_preparation import analyze_book_text, format_preparation_report


def test_preparation_report_flags_review_items():
    raw = "Title\f\fContents\nwww.example.com\n[1]\n" + ("A" * 2600)
    cleaned = "Contents\n\nwww.example.com\n\n" + ("A" * 2600)
    report = analyze_book_text(raw, cleaned, "book.pdf")

    codes = {item["code"] for item in report["issues"]}
    assert "blank_pages" in codes
    assert "long_paragraphs" in codes
    assert "web_addresses" in codes
    assert "BOOK PREPARATION REPORT" in format_preparation_report(report)
