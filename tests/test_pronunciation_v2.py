import json

from core.pronunciation import PronunciationDictionary


def test_legacy_pronunciation_file_is_migrated_and_preserved(tmp_path):
    path = tmp_path / "pronunciation.json"
    path.write_text(json.dumps({"Dr.": "Doctor"}), encoding="utf-8")
    dictionary = PronunciationDictionary(path)

    assert dictionary.replace("Dr. Cruz met Dr. Lim.") == "Doctor Cruz met Doctor Lim."
    dictionary.save()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema"] == 2
    assert saved["rules"][0]["source"] == "Dr."


def test_whole_word_rule_does_not_change_longer_words(tmp_path):
    dictionary = PronunciationDictionary(tmp_path / "rules.json")
    dictionary.add("St", "Saint", whole_word=True, case_sensitive=False)
    assert dictionary.replace("St John stood still.") == "Saint John stood still."


def test_duplicate_rule_snapshot_is_applied_only_once(tmp_path):
    dictionary = PronunciationDictionary(tmp_path / "rules.json")
    rule_id = dictionary.add("a", "aa", whole_word=False, case_sensitive=True)
    snapshot = dictionary.list_rules()
    assert snapshot[0]["id"] == rule_id
    assert dictionary.replace("a", extra_rules=snapshot) == "aa"


def test_language_specific_rules_use_book_language(tmp_path):
    dictionary = PronunciationDictionary(tmp_path / "rules.json")
    dictionary.add("Roma", "Rome", language="en")
    dictionary.add("Roma", "Roma", language="tl")
    assert dictionary.replace("Roma", language="en") == "Rome"
    assert dictionary.replace("Roma", language="tl") == "Roma"
