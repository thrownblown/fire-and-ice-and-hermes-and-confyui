from core.script import Cue, merge_sentences, parse_script

SAMPLE = (
    "Scripts.com\n"
    "Fire And Ice\n"
    "By Roy Thomas\n"
    "*Page 1/10*\n"
    "And her ambition was to extend her realm...\n"
    "*Page 2/10*\n"
    "- Perhaps. You will present our demands...\n"
)


def test_empty_text_returns_no_cues():
    assert parse_script("") == []


def test_headers_are_skipped():
    texts = [c.text for c in parse_script(SAMPLE)]
    for h in ("Scripts.com", "Fire And Ice", "By Roy Thomas"):
        assert h not in texts


def test_page_numbers_are_tracked():
    cues = parse_script(SAMPLE)
    assert cues[0].page == 1
    assert cues[1].page == 2


def test_text_preserved_verbatim():
    cues = parse_script("And her ambition was to extend her realm... to all the regions")
    assert cues[0].text == "And her ambition was to extend her realm... to all the regions"


def test_bare_page_number_is_skipped():
    cues = parse_script("*Page 1/10*\n1\nAnd her ambition was to extend...\n")
    assert [c.text for c in cues] == ["And her ambition was to extend..."]
    assert cues[0].page == 1


def test_merge_sentences():
    cues = [
        Cue(0, 1, "And her ambition was to extend her realm..."),
        Cue(1, 1, "to all the regions of the known world."),
        Cue(2, 1, "To this end, she gathered an army."),
    ]
    merged = merge_sentences(cues)
    assert len(merged) == 2
    assert merged[0].text == "And her ambition was to extend her realm... to all the regions of the known world."
    assert merged[1].text == "To this end, she gathered an army."


def test_merge_strips_speaker_marker():
    cues = [Cue(0, 1, "- Perhaps. You will present our demands..."), Cue(1, 1, "- No!")]
    merged = merge_sentences(cues)
    assert merged[0].text.startswith("Perhaps")
    assert not merged[0].text.startswith("-")
