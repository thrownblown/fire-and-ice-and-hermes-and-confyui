from core.ledger import normalize_location, normalize_person, is_unreliable


def test_location_collapses_ice_cave_synonyms():
    assert normalize_location("Ice cave") == "ice_cave"
    assert normalize_location("icy cavern") == "ice_cave"


def test_location_cottage_family():
    assert normalize_location("wooden cabin interior") == "cottage"
    assert normalize_location("cottage") == "cottage"


def test_person_tokens_are_sorted_and_stable():
    a = normalize_person({"sex": "female", "hair": "long black", "clothing": "purple top"})
    b = normalize_person({"sex": "Female", "hair": "long, black", "clothing": "purple top"})
    assert a == b
    assert "hair:long_black" in a


def test_identical_people_are_unreliable():
    people = [
        {"sex": "male", "clothing": "black loincloth"},
        {"sex": "male", "clothing": "black loincloth"},
    ]
    assert is_unreliable(3, 0, people) is True


def test_distinct_people_are_reliable():
    people = [
        {"sex": "female", "hair": "long black"},
        {"sex": "male", "hair": "blond"},
    ]
    assert is_unreliable(1, 1, people) is False
