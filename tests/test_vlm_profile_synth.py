import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "vlm_profile_synth", ROOT / "tools" / "vlm_profile_synth.py")
mod = importlib.util.module_from_spec(_spec)
sys.modules["vlm_profile_synth"] = mod
_spec.loader.exec_module(mod)


def row(char, lens, js, ok=True, image="refs/characters/X/a.jpg", ts="2026-10-14T00:00:00Z"):
    return {"ts": ts, "char": char, "lens": lens, "image": image, "model": "m",
            "ok": ok, "attempts": 1, "text": json.dumps(js) if js is not None else "junk",
            "json": js}


HAIR_BLACK = {"color": "black", "length": "long", "texture": "straight", "style": "loose", "notes": None}
HAIR_BLACK2 = {"color": "Black", "length": "long", "texture": "straight", "style": "loose", "notes": None}
HAIR_BROWN = {"color": "brown", "length": "long", "texture": "straight", "style": "loose", "notes": None}


@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "manifests" / "vlm_charpass.jsonl"
    p.parent.mkdir(parents=True)
    rows = [
        row("TUTOR", "hair", HAIR_BLACK, image="refs/characters/TUTOR/a.jpg"),
        row("TUTOR", "hair", HAIR_BLACK2, image="refs/characters/TUTOR/b.jpg"),
        row("TUTOR", "hair", HAIR_BROWN, image="refs/characters/TUTOR/c.jpg"),
        row("TUTOR", "physique", {"sex": "male", "age_range": "elderly", "build": "muscular",
                                  "height_impression": "tall", "skin_neutral_light": "tan"},
            image="refs/characters/TUTOR/a.jpg"),
        row("TUTOR", "physique", {"sex": "male", "age_range": "elderly", "build": "muscular",
                                  "height_impression": "tall", "skin_neutral_light": "tan"},
            image="refs/characters/TUTOR/b.jpg"),
        row("TUTOR", "physique", {"sex": "male", "age_range": "middle-aged", "build": "stocky",
                                  "height_impression": "tall", "skin_neutral_light": "tan"},
            image="refs/characters/TUTOR/c.jpg"),
        row("TEEGRA", "hair", {"color": "red", "length": "very long", "texture": "wavy",
                               "style": "loose", "notes": None},
            image="refs/characters/TEEGRA/a.jpg"),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return tmp_path


# ---- ledger loading ------------------------------------------------------------

def test_load_ledger_skips_bad_lines(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_text(json.dumps(row("A", "hair", HAIR_BLACK)) + "\n{broken\n\n"
                 + json.dumps(row("A", "hair", HAIR_BROWN)) + "\n", encoding="utf-8")
    rows = mod.load_ledger(str(p))
    assert len(rows) == 2


def test_failed_rows_excluded_from_synthesis(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    rows.append(row("TUTOR", "hair", None, ok=False))
    rows.append(row("TUTOR", "hair", {"color": "green", "length": "long", "texture": "straight",
                                      "style": "loose", "notes": None}, ok=False))
    prof = mod.synthesize([r for r in rows], "TUTOR")
    assert prof["rows"]["ok"] == 6           # only ok rows with json
    colors = [v for v in prof["lenses"]["hair"]["color"]["all_values"]]
    assert "green" not in colors


# ---- string-trait consensus ------------------------------------------------------

def test_string_trait_majority_is_stable(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    prof = mod.synthesize(rows, "TUTOR")
    hair_color = prof["lenses"]["hair"]["color"]
    assert hair_color["value"] == "black"
    assert abs(hair_color["share"] - 2 / 3) < 1e-9
    assert hair_color["stable"] is True


def test_profile_summary_sections_list_stable_and_disputed(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    prof = mod.synthesize(rows, "TUTOR")
    # stable section names "lens.trait" for every stable string trait
    assert "hair.color" in prof["stable"]
    assert "physique.sex" in prof["stable"]
    # a true split lands in disputed
    assert all(not d.startswith("hair.color") for d in prof["disputed"])


def test_true_split_is_disputed(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "hair", HAIR_BLACK),
        row("A", "hair", {"color": "blond", "length": "long", "texture": "straight", "style": "loose", "notes": None}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    c = prof["lenses"]["hair"]["color"]
    assert c["stable"] is False
    assert c["share"] == 0.5
    assert sorted(c["all_values"]) == ["black", "blond"]


def test_trait_none_values_are_skipped_in_vote(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    prof = mod.synthesize(rows, "TUTOR")
    notes = prof["lenses"]["hair"]["notes"]
    assert notes["n"] == 0                   # all three answered null
    assert notes["value"] is None
    assert notes["stable"] is False


# ---- list + objlist traits ---------------------------------------------------------

def test_list_trait_frequency(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "face", {"face_shape": "oval", "eyes": None, "brows": None, "nose": None,
                          "lips": None, "distinguishing_features": ["scar on cheek", "bushy brows"]}),
        row("A", "face", {"face_shape": "oval", "eyes": None, "brows": None, "nose": None,
                          "lips": None, "distinguishing_features": ["scar on cheek"]}),
        row("A", "face", {"face_shape": "oval", "eyes": None, "brows": None, "nose": None,
                          "lips": None, "distinguishing_features": ["gold tooth"]}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    feats = prof["lenses"]["face"]["distinguishing_features"]
    assert feats["kind"] == "list"
    assert feats["stable_items"] == ["scar on cheek"]           # 2/3
    assert sorted(feats["disputed_items"]) == ["bushy brows", "gold tooth"]  # 1/3 each


def test_objlist_trait_groups_by_item_name(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "wardrobe", {"garments": [{"item": "cloak", "color": "brown", "material": "fur", "cut": "full"},
                                           {"item": "tunic", "color": "blue", "material": "cloth", "cut": "loose"}],
                              "state_of_dress": "fully dressed"}),
        row("A", "wardrobe", {"garments": [{"item": "cloak", "color": "brown", "material": "fur", "cut": "full"}],
                              "state_of_dress": "fully dressed"}),
        row("A", "wardrobe", {"garments": [{"item": "cloak", "color": "grey", "material": "fur", "cut": "full"}],
                              "state_of_dress": "fully dressed"}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    g = prof["lenses"]["wardrobe"]["garments"]
    assert g["kind"] == "objlist"
    assert g["stable_items"] == ["cloak"]            # present in 3/3 rows (any color)
    assert g["disputed_items"] == ["tunic"]          # 1/3
    # per-item detail records the color disagreement
    cloak = g["detail"]["cloak"]
    assert cloak["n"] == 3
    assert "brown" in cloak["values"] and "grey" in cloak["values"]


# ---- profile shape + determinism ----------------------------------------------------

def test_profile_is_deterministic(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    a = mod.synthesize(rows, "TUTOR")
    b = mod.synthesize(rows, "TUTOR")
    a.pop("generated"); b.pop("generated")
    assert a == b


def test_traits_alphabetical_within_lens(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    prof = mod.synthesize(rows, "TUTOR")
    assert list(prof["lenses"]["hair"]) == sorted(prof["lenses"]["hair"])


def test_prompt_block_composes_stable_traits(ledger):
    rows = mod.load_ledger(str(ledger / "manifests" / "vlm_charpass.jsonl"))
    prof = mod.synthesize(rows, "TUTOR")
    pb = prof["prompt_block"]
    assert isinstance(pb, str) and pb
    assert "black" in pb.lower()        # stable hair color
    assert "male" in pb.lower()         # stable sex
    assert "muscular" in pb.lower()     # stable build


def test_prompt_block_omits_single_answer_traits(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [row("A", "hair", HAIR_BLACK), row("A", "hair", HAIR_BROWN)]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    assert prof["prompt_block"] == "" or "brown" not in prof["prompt_block"].lower()


# ---- CLI: file outputs ----------------------------------------------------------------

def test_cli_writes_json_and_md(ledger):
    rc = mod.run_synth(["--char", "TUTOR", "--root", str(ledger)])
    assert rc == 0
    pj = ledger / "library" / "char" / "profiles" / "TUTOR.json"
    pm = ledger / "library" / "char" / "profiles" / "TUTOR.md"
    assert pj.exists() and pm.exists()
    prof = json.loads(pj.read_text(encoding="utf-8"))
    assert prof["char"] == "TUTOR"
    assert "prompt_block" in prof
    md = pm.read_text(encoding="utf-8")
    assert "TUTOR" in md and "## Prompt block" in md
    assert "black" in md


def test_cli_all_writes_every_char(ledger):
    rc = mod.run_synth(["--all", "--root", str(ledger)])
    assert rc == 0
    assert (ledger / "library" / "char" / "profiles" / "TUTOR.json").exists()
    assert (ledger / "library" / "char" / "profiles" / "TEEGRA.json").exists()


def test_cli_unknown_char_errors(ledger):
    rc = mod.run_synth(["--char", "NOBODY", "--root", str(ledger)])
    assert rc == 2


def test_cli_custom_ledger_path(ledger, tmp_path):
    other = tmp_path / "other.jsonl"
    other.write_text(json.dumps(row("SOLO", "hair", HAIR_BLACK)) + "\n", encoding="utf-8")
    rc = mod.run_synth(["--char", "SOLO", "--ledger", str(other), "--root", str(ledger)])
    assert rc == 0
    assert (ledger / "library" / "char" / "profiles" / "SOLO.json").exists()


def test_empty_ledger_errors(ledger):
    empty = ledger / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    rc = mod.run_synth(["--all", "--ledger", str(empty), "--root", str(ledger)])
    assert rc == 2


# ---- extra edge cases ----------------------------------------------------------

def test_duplicate_items_within_one_row_count_once(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "face", {"face_shape": None, "eyes": None, "brows": None, "nose": None,
                          "lips": None, "distinguishing_features": ["scar", "scar", "scar"]}),
        row("A", "face", {"face_shape": None, "eyes": None, "brows": None, "nose": None,
                          "lips": None, "distinguishing_features": ["scar"]}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    feats = prof["lenses"]["face"]["distinguishing_features"]
    assert feats["counts"] == {"scar": 2}        # per-row, not per-occurrence
    assert feats["stable_items"] == ["scar"]


def test_objlist_without_item_key_falls_back(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "wardrobe", {"garments": [{"color": "brown", "material": "fur"}], "state_of_dress": None}),
        row("A", "wardrobe", {"garments": [{"color": "brown", "material": "fur"}], "state_of_dress": None}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    g = prof["lenses"]["wardrobe"]["garments"]
    assert len(g["stable_items"]) == 1
    assert g["n_rows"] == 2


def test_share_boundary_exactly_0_6_is_stable(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [row("A", "hair", HAIR_BLACK)] * 3 + [row("A", "hair", HAIR_BROWN)] * 2
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    c = prof["lenses"]["hair"]["color"]
    assert c["share"] == 0.6
    assert c["stable"] is True


def test_char_with_zero_ok_rows_yields_empty_profile(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [row("A", "hair", None, ok=False)]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    assert prof["lenses"] == {}
    assert prof["stable"] == [] and prof["disputed"] == []
    assert prof["prompt_block"] == ""
    assert prof["rows"] == {"total": 1, "ok": 0}


def test_prompt_block_includes_signature_and_weapons(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "signature", {"memorable_traits": ["long white hair", "fur cloak"],
                               "unmistakable_because": "the white hair against the fur"}),
        row("A", "signature", {"memorable_traits": ["long white hair"],
                               "unmistakable_because": "the white hair against the fur"}),
        row("A", "props", {"items": [], "weapons": ["broad sword"]}),
        row("A", "props", {"items": [], "weapons": ["broad sword"]}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    pb = prof["prompt_block"]
    assert "long white hair" in pb
    assert "broad sword" in pb
    assert "unmistakable" in pb


def test_render_md_disputed_section_shares(tmp_path):
    p = tmp_path / "l.jsonl"
    rows = [row("A", "hair", HAIR_BLACK), row("A", "hair", HAIR_BROWN)]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    md = mod.render_md(prof)
    assert "## Disputed traits" in md
    assert "hair.color" in md
    assert "share 0.50" in md


def test_no_selection_flag_errors(ledger):
    rc = mod.run_synth(["--root", str(ledger)])
    assert rc == 2


def test_rerun_overwrites_profiles_idempotently(ledger):
    mod.run_synth(["--char", "TUTOR", "--root", str(ledger)])
    pj = ledger / "library" / "char" / "profiles" / "TUTOR.json"
    first = json.loads(pj.read_text(encoding="utf-8"))
    mod.run_synth(["--char", "TUTOR", "--root", str(ledger)])
    second = json.loads(pj.read_text(encoding="utf-8"))
    first.pop("generated"); second.pop("generated")
    assert first == second


def test_nullish_string_values_excluded_from_vote(tmp_path):
    # pre-fix ledger rows (smoke run) may carry "null" as a string value
    p = tmp_path / "l.jsonl"
    rows = [
        row("A", "colors", {"skin": "tan", "hair": "black", "eyes": None,
                            "garment_primary": "blue", "garment_secondary": "null",
                            "metal_accent": "N/A"}),
        row("A", "colors", {"skin": "tan", "hair": "black", "eyes": "brown",
                            "garment_primary": "blue", "garment_secondary": None,
                            "metal_accent": None}),
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    prof = mod.synthesize(mod.load_ledger(str(p)), "A")
    gs = prof["lenses"]["colors"]["garment_secondary"]
    assert gs["n"] == 0 and gs["value"] is None
    assert "null" not in gs["all_values"]
    ma = prof["lenses"]["colors"]["metal_accent"]
    assert ma["n"] == 0
