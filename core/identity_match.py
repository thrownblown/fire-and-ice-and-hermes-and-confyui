"""Match a VLM appearance description to one of the named subjects — one scorer, used twice.

`_shot_presence()` in `runs/build_technicolor_audio_only.py` needs to say "this is JULIANA" in a
prompt; `tools/check_name_stamps.py` audits `manifests/character_names.jsonl`. They must agree, so the
scoring lives here rather than in either caller.

**Its accuracy is bounded, and the bound matters.** A plain content-word overlap scorer was tried
first and it asserted nonsense: "long white hair, dark robe" (Nekron, male) came back as JULIANA,
because her canon text contains robe/purple/black too. Hair colour and sex are the two things a VLM
still read is reliable about, so they are HARD vetoes here and colour agreement scores extra.

What it still cannot do: separate two women who share pale skin, long black hair and a purple
garment. Measured 2026-11-05 on scene S03 — Juliana (Nekron's mother, in the purple gown) and Teegra
(the heroine, in a purple two-piece) both score as TEEGRA against shots 00067/00069/00071, and the
scene's own dialogue is mother-and-son (`script/dialogue-timeline.tsv`: "You have done well, my son"
/ "I want to thank you, Mother"), which says those faces should be Juliana. That question is OPEN —
it needs a look at the frames, not a scorer. Do not read agreement out of this module as proof of a
stamp; read disagreement ON SEX OR HAIR COLOUR as evidence.
"""
from __future__ import annotations

import re

MIN_SCORE = 2
_STOP = {"with", "and", "the", "long", "short", "dark", "light", "very", "deep", "black", "hair"}

# Sex per character, loaded from refs/character_sex.json. The canon text does NOT state sex ("very long
# black hair, pale skin, ..."), so inferring it from prose left the veto blind and let a male figure with
# spiky black hair match TEEGRA. An explicit table is the only reliable source here.
SEX_OVERRIDE: dict[str, str | None] = {}


def load_sex_table(path=None) -> dict[str, str]:
    """Populate SEX_OVERRIDE from refs/character_sex.json (idempotent, safe to call more than once)."""
    global SEX_OVERRIDE
    from pathlib import Path
    import json as _json
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "refs" / "character_sex.json"
    if not p.exists():
        return SEX_OVERRIDE
    data = _json.loads(p.read_text(encoding="utf-8"))
    SEX_OVERRIDE = {str(k).upper(): (v if v in ("f", "m") else None)
                    for k, v in (data.get("sex") or {}).items()}
    return SEX_OVERRIDE


def canon_sex(name: str, traits_text: str | None) -> str | None:
    """Sex for a character: the explicit table first, prose second, None if neither says."""
    if not SEX_OVERRIDE:
        load_sex_table()
    explicit = SEX_OVERRIDE.get(str(name).upper())
    if explicit:
        return explicit
    return sex_of(traits_text)


def hair_colour_headline(traits_text: str | None) -> str | None:
    """Hair colour from the HAIR PHRASE only (the text up to the first comma).

    Scanning the whole canon text picked up unrelated colours — LARN came out "white" because his entry
    mentions a white armband — which both vetoes the right candidate and matches the wrong one.
    """
    t = (traits_text or "")
    head = t.split(",")[0]
    return hair_colour(head)

# Hair colour must be a HARD discriminator, not one token among many. First pass without it called a
# "long white hair dark robe" (Nekron, male) "JULIANA", because JULIANA's traits text contains the
# words robe/purple/black too. Colour + sex are the two things a VLM read is reliable about.
_HAIR_COLOURS = ("white", "silver", "grey", "gray", "black", "blond", "blonde", "red", "brown",
                 "auburn", "golden")
_FEMALE = ("female", "woman", "women", "girl", "she", "her", "mother", "queen", "princess", "sorceress")
_MALE = ("male", "man", "men", "boy", "he", "him", "his", "father", "king", "warrior", "lord")


def hair_colour(text: str | None) -> str | None:
    t = (text or "").lower()
    for c in _HAIR_COLOURS:
        if c in t:
            return "grey" if c in ("gray", "silver") else c
    return None


def sex_of(text: str | None) -> str | None:
    """'f' / 'm' / None from free text, using WORD BOUNDARIES.

    Substring counting was silently useless: "male" is inside "female", so every 'female' record scored
    one hit each way and returned None — the sex veto then never fired, and 45 name assignments landed on
    figures of the opposite sex (TEEGRA/LARN on male frames). Regex word boundaries fix it.
    """
    t = (text or "").lower()
    if not t.strip():
        return None
    f = sum(1 for w in _FEMALE if re.search(rf"\b{re.escape(w)}\b", t))
    m = sum(1 for w in _MALE if re.search(rf"\b{re.escape(w)}\b", t))
    if f > m:
        return "f"
    if m > f:
        return "m"
    return None


def content_words(*texts) -> set[str]:
    out: set[str] = set()
    for t in texts:
        for tok in re.findall(r"[a-z]+", (t or "").lower()):
            if len(tok) > 3 and tok not in _STOP:
                out.add(tok)
    return out


def match_subject(desc: str | None, candidates, traits: dict[str, str],
                  hair: str | None = None, sex: str | None = None) -> tuple[str | None, int]:
    """Best `(subject_name, score)` for a description against candidate names.

    `desc` is normally `hair + " " + clothing` from a `character_pass.jsonl` person record; pass the
    record's own `hair` and `sex` fields too when you have them, so colour/sex can veto a candidate.
    """
    words = content_words(desc)
    hair = hair if hair is not None else desc
    if not words:
        return None, 0
    want_colour = hair_colour(hair)
    best, best_score = None, 0
    for name in candidates:
        tr = (traits.get(name) or "").lower()
        if not tr:
            continue
        # veto: a colour or sex we can read off the description that contradicts the canon text
        if want_colour:
            have = hair_colour_headline(tr)          # hair phrase only — not every colour in the entry
            if have and have != want_colour:
                continue
        if sex:
            cand_sex = canon_sex(name, tr)           # explicit table first; prose is unreliable
            if cand_sex and cand_sex != sex:
                continue
        score = sum(1 for w in words if w in tr)
        if want_colour and want_colour in tr:
            score += 2                                  # colour agreement is worth more than a word
        if score > best_score:
            best, best_score = name, score
    return best, best_score


def assertable(desc: str | None, candidates, traits: dict[str, str],
               hair: str | None = None, sex: str | None = None) -> str | None:
    """The subject name, or None when the evidence is too weak to assert one."""
    name, score = match_subject(desc, candidates, traits, hair=hair, sex=sex)
    return name if name and score >= MIN_SCORE else None
