import json

from core.vlm_charpass import LENSES, build_messages, normalize, consensus


# ---- LENSES ---------------------------------------------------------------

def test_lenses_are_the_seven_named_in_order():
    assert list(LENSES) == ["physique", "face", "hair", "wardrobe", "props", "colors", "signature"]


def test_each_lens_has_schema_and_instruction():
    for name, spec in LENSES.items():
        assert isinstance(spec["schema"], dict) and spec["schema"], name
        assert isinstance(spec["instruction"], str) and spec["instruction"].strip(), name


# ---- build_messages -------------------------------------------------------

def test_build_messages_shape_is_vision_chat():
    msgs = build_messages("hair", "B64DATA")
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    content = msgs[1]["content"]
    assert content[0] == {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,B64DATA"}}
    assert content[1]["type"] == "text"
    assert LENSES["hair"]["instruction"] in content[1]["text"]


def test_system_prompt_carries_invariants():
    msgs = build_messages("physique", "X")
    sys_text = msgs[0]["content"]
    low = sys_text.lower()
    assert "neutral light" in low          # skin under neutral light
    assert "never name" in low or "do not name" in low
    assert "strict json" in low
    assert "fences" in low or "markdown" in low


def test_system_prompt_includes_lens_schema():
    msgs = build_messages("colors", "X")
    sys_text = msgs[0]["content"]
    for key in LENSES["colors"]["schema"]:
        assert key in sys_text


# ---- normalize ------------------------------------------------------------

def test_normalize_parses_plain_json():
    text = '{"color": "black", "length": "long", "texture": "straight", "style": "loose", "notes": "bangs"}'
    out = normalize("hair", text)
    assert out == {"color": "black", "length": "long", "texture": "straight", "style": "loose", "notes": "bangs"}


def test_normalize_empty_string_answer_becomes_none():
    out = normalize("hair", '{"color": "black", "notes": ""}')
    assert out["notes"] is None


def test_normalize_strips_markdown_fences_and_prose():
    text = 'Sure! Here is the JSON:\n```json\n{"color": "red", "length": "short", "texture": "curly", "style": "bob", "notes": null}\n```\nHope that helps.'
    out = normalize("hair", text)
    assert out["color"] == "red"
    assert out["length"] == "short"


def test_normalize_fills_missing_schema_keys_as_none():
    out = normalize("hair", '{"color": "blond"}')
    assert out["color"] == "blond"
    for key in LENSES["hair"]["schema"]:
        assert key in out


def test_normalize_keeps_extra_keys_under_extra():
    out = normalize("hair", '{"color": "blond", "smell": "pine"}')
    assert out["_extra"] == {"smell": "pine"}


def test_normalize_returns_none_on_junk():
    assert normalize("hair", "I cannot see an image.") is None
    assert normalize("hair", "") is None


def test_normalize_returns_none_when_no_object_found():
    assert normalize("hair", "[1, 2, 3]") is None


def test_normalize_list_field_coerced_to_list():
    out = normalize("face", '{"face_shape": "oval", "distinguishing_features": "scar on cheek"}')
    assert out["distinguishing_features"] == ["scar on cheek"]


def test_normalize_preserves_list_field():
    out = normalize("signature", '{"memorable_traits": ["white hair", "fur cloak"], "unmistakable_because": "the white hair"}')
    assert out["memorable_traits"] == ["white hair", "fur cloak"]


# ---- consensus ------------------------------------------------------------

def test_consensus_majority_vote():
    c = consensus(["black", "black", "brown"])
    assert c["value"] == "black"
    assert c["n"] == 3
    assert abs(c["share"] - 2 / 3) < 1e-9
    assert c["outliers"] == ["brown"]


def test_consensus_lowercase_collapse():
    c = consensus(["Black", "black", "BLACK"])
    assert c["value"] == "black"
    assert c["share"] == 1.0
    assert c["outliers"] == []


def test_consensus_substring_merge():
    c = consensus(["long black", "long, straight, black hair", "long black hair"])
    assert c["value"] == "long black"   # canonical = the shortest merged form
    assert c["share"] == 1.0
    assert c["outliers"] == []


def test_consensus_tie_breaks_deterministically():
    c = consensus(["b", "a"])
    assert c["value"] == "a"   # equal counts -> alphabetically first canonical
    assert c["share"] == 0.5


def test_consensus_empty_list():
    c = consensus([])
    assert c == {"value": None, "share": 0.0, "n": 0, "outliers": []}


def test_consensus_outliers_keep_original_casing():
    c = consensus(["black", "black", "Silver"])
    assert c["outliers"] == ["Silver"]


# ---- edge cases: normalize -------------------------------------------------

def test_normalize_unknown_lens_raises():
    import pytest
    with pytest.raises(KeyError):
        normalize("nope", "{}")


def test_build_messages_unknown_lens_raises():
    import pytest
    with pytest.raises(KeyError):
        build_messages("nope", "X")


def test_normalize_skips_unparseable_braces_before_real_object():
    text = 'Here is {not json at all} and then {"color": "red", "length": "short", "texture": "curly", "style": "bald", "notes": ""}'
    out = normalize("hair", text)
    assert out is not None
    assert out["color"] == "red"


def test_normalize_handles_escaped_quotes_inside_strings():
    text = r'{"memorable_traits": ["the \"ice\" crown"], "unmistakable_because": "crown"}'
    out = normalize("signature", text)
    assert out["memorable_traits"] == ['the "ice" crown']


def test_normalize_first_object_wins_when_two_present():
    text = '{"color": "red"} some prose {"color": "blue"}'
    out = normalize("hair", text)
    assert out["color"] == "red"


def test_normalize_truncated_json_returns_none():
    assert normalize("hair", '{"color": "red", "length": ') is None


def test_normalize_str_field_number_coerced_to_string():
    out = normalize("physique", '{"sex": "male", "age_range": 30, "build": "lean", "height_impression": "tall", "skin_neutral_light": "tan"}')
    assert out["age_range"] == "30"


def test_normalize_explicit_null_kept_as_none():
    out = normalize("colors", '{"skin": "tan", "hair": null}')
    assert out["hair"] is None
    assert out["eyes"] is None  # missing == null too


def test_normalize_objlist_string_is_not_a_list():
    out = normalize("wardrobe", '{"garments": "a fur cloak", "state_of_dress": "clothed"}')
    assert out["garments"] is None


def test_normalize_objlist_dict_wrapped_into_list():
    out = normalize("wardrobe", '{"garments": {"item": "cloak", "color": "brown"}, "state_of_dress": "clothed"}')
    assert out["garments"] == [{"item": "cloak", "color": "brown"}]


def test_normalize_wardrobe_full_shape_roundtrip():
    text = json.dumps({
        "garments": [
            {"item": "tunic", "color": "blue", "material": "cloth", "cut": "loose"},
            {"item": "belt", "color": "brown", "material": "leather", "cut": "waist"},
        ],
        "state_of_dress": "fully dressed",
    })
    out = normalize("wardrobe", text)
    assert len(out["garments"]) == 2
    assert "_extra" not in out


def test_normalize_empty_list_fields_stay_empty():
    out = normalize("props", '{"items": [], "weapons": []}')
    assert out["items"] == []
    assert out["weapons"] == []


def test_normalize_props_string_weapon_becomes_list():
    out = normalize("props", '{"items": [], "weapons": "a broadsword"}')
    assert out["weapons"] == ["a broadsword"]


def test_normalize_empty_string_list_field_becomes_empty_list():
    out = normalize("face", '{"distinguishing_features": "  "}')
    assert out["distinguishing_features"] == []


def test_normalize_null_placeholder_strings_become_none():
    # observed in the real smoke run: "null" as a STRING value
    out = normalize("colors", '{"skin": "tan", "garment_secondary": "null", "metal_accent": "None", "eyes": "N/A"}')
    assert out["garment_secondary"] is None
    assert out["metal_accent"] is None
    assert out["eyes"] is None
    assert out["skin"] == "tan"


# ---- edge cases: consensus -------------------------------------------------

def test_consensus_filters_non_strings_and_none():
    c = consensus(["black", None, 42, "", "black"])
    assert c["n"] == 2
    assert c["value"] == "black"
    assert c["share"] == 1.0


def test_consensus_single_value():
    c = consensus(["only one"])
    assert c["value"] == "only one"
    assert c["share"] == 1.0
    assert c["n"] == 1
    assert c["outliers"] == []


def test_consensus_all_distinct_picks_alphabetical():
    c = consensus(["zulu", "alpha", "mike"])
    assert c["value"] == "alpha"
    assert abs(c["share"] - 1 / 3) < 1e-9
    assert sorted(c["outliers"]) == ["mike", "zulu"]


def test_consensus_merges_across_case_and_punctuation():
    c = consensus(["Long Black", "long-black", "LONG  BLACK!"])
    assert c["value"] == "long black"
    assert c["share"] == 1.0


def test_consensus_subset_merge_keeps_shortest_surface():
    c = consensus(["black hair", "black", "black"])
    # {black} subset of {black,hair}: all merge; canonical = shortest surface
    assert c["value"] == "black"
    assert c["share"] == 1.0
    assert c["n"] == 3


def test_consensus_digits_survive_canon_key():
    c = consensus(["sword about 3 feet long", "sword about 3 feet long"])
    assert c["value"] == "sword about 3 feet long"
    assert c["share"] == 1.0


def test_consensus_punctuation_only_values_dropped():
    c = consensus(["???", "...", "real value"])
    assert c["n"] == 1
    assert c["value"] == "real value"


def test_consensus_deterministic_on_repeat():
    vals = ["long black", "brown", "long, straight, black hair", "black"]
    assert consensus(vals) == consensus(vals)


def test_consensus_three_way_split_share():
    c = consensus(["a", "a", "a", "b", "b", "c"])
    assert c["value"] == "a"
    assert c["share"] == 0.5
    assert c["n"] == 6
    assert sorted(c["outliers"]) == ["b", "b", "c"]
