"""Acceptance tests for the asset lookup / reference-image packing tool.

Run:  .venv/Scripts/python.exe -m pytest tests/test_asset_lookup.py -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import asset_library as al  # noqa: E402

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "assets")


def _char_manifest(tmp_path, character_id="x", status="approved"):
    d = tmp_path / "characters" / character_id
    (d / "refs").mkdir(parents=True)
    manifest = {
        "schema": "fni.asset/character/v1",
        "character_id": character_id,
        "name": character_id.title(),
        "status": status,
        "version": 1,
        "canonical_refs": {
            "face": {"front": "refs/face.front.png", "profile": "refs/face.profile.png"},
            "body": {"front": "refs/body.front.png", "back": "refs/body.back.png"},
        },
    }
    (d / "manifest.yml").write_text(_yaml(manifest), encoding="utf-8")
    for rel in ("face.front.png", "face.profile.png", "body.front.png", "body.back.png"):
        (d / "refs" / rel).write_bytes(b"png")
    return manifest


def _garment(tmp_path, character_id, garment_id, status="approved", refs=None):
    d = tmp_path / "characters" / character_id / "wardrobe" / garment_id
    (d / "refs").mkdir(parents=True)
    refs = refs or {"front": "refs/front.png", "back": "refs/back.png", "side": "refs/side.png"}
    manifest = {
        "schema": "fni.asset/garment/v1",
        "garment_id": garment_id,
        "character_id": character_id,
        "name": garment_id,
        "slot": garment_id.split(".")[1],
        "version": 1,
        "status": status,
        "refs": dict(refs),
    }
    (d / "manifest.yml").write_text(_yaml(manifest), encoding="utf-8")
    for rel in refs.values():
        (d / rel).write_bytes(b"png")
    return manifest


def _prop(tmp_path, prop_id, status="approved", refs=None):
    d = tmp_path / "props" / prop_id
    (d / "refs").mkdir(parents=True)
    refs = refs or {"front": "refs/front.png", "side": "refs/side.png"}
    manifest = {
        "schema": "fni.asset/prop/v1",
        "prop_id": prop_id,
        "name": prop_id,
        "category": prop_id.split(".")[0],
        "version": 1,
        "status": status,
        "refs": dict(refs),
    }
    (d / "manifest.yml").write_text(_yaml(manifest), encoding="utf-8")
    for rel in refs.values():
        (d / rel).write_bytes(b"png")
    return manifest


def _yaml(d):
    import yaml
    return yaml.safe_dump(d)


# --- happy path (real sample library) -------------------------------------------

def test_example_happy_path():
    pack = al.build_pack(root=SAMPLE, character_ids=["aria"], wardrobe=["coat_02"],
                         props=["lantern_01"])
    assert pack["validation"]["ok"]
    refs = pack["reference_images"]
    assert len(refs) == 11
    assert [r["role"] for r in refs[:4]] == ["character"] * 4
    assert [r["angle"] for r in refs[:4]] == ["face.front", "face.profile",
                                              "body.front", "body.back"]
    # garment resolves coat_02 -> aria.outerwear.coat_02
    garment = [r for r in refs if r["role"] == "wardrobe"][0]["asset_id"]
    assert garment == "aria.outerwear.coat_02"
    prop = [r for r in refs if r["role"] == "prop"][0]["asset_id"]
    assert prop == "set-dressing.lantern_01"
    assert "charcoal" in pack["description_block"]
    assert pack["request"]["character_ids"] == ["aria"]


def test_shot_mode():
    pack = al.build_pack(root=SAMPLE, shot_id="shot:00023")
    assert pack["validation"]["ok"]
    ids = {r["asset_id"] for r in pack["reference_images"]}
    assert "aria" in ids
    assert "aria.outerwear.coat_02" in ids
    assert "aria.shoes.boots" in ids
    assert "set-dressing.lantern_01" in ids


def test_full_ids_without_character_flag():
    pack = al.build_pack(root=SAMPLE, wardrobe=["aria.outerwear.coat_02"],
                         props=["set-dressing.lantern_01"])
    assert pack["validation"]["ok"]


# --- failure modes (real sample library) ----------------------------------------

def test_draft_garment_rejected():
    with pytest.raises(al.AssetLookupError) as e:
        al.build_pack(root=SAMPLE, character_ids=["aria"], wardrobe=["leggings"])
    assert any("not approved" in err for err in e.value.errors)


def test_missing_character_rejected():
    with pytest.raises(al.AssetLookupError) as e:
        al.build_pack(root=SAMPLE, character_ids=["nobody"])
    assert any("missing manifest" in err for err in e.value.errors)


def test_missing_prop_rejected():
    with pytest.raises(al.AssetLookupError) as e:
        al.build_pack(root=SAMPLE, character_ids=["aria"], props=["nope_thing"])
    assert any("no prop" in err for err in e.value.errors)


# --- failure modes (fixtures) ----------------------------------------------------

def test_missing_reference_file(tmp_path):
    cid, gid = "x", "x.outerwear.coat"
    _char_manifest(tmp_path, character_id=cid)
    m = _garment(tmp_path, cid, gid, status="approved",
                 refs={"front": "refs/front.png", "back": "refs/back.png",
                       "side": "refs/side.png"})
    # delete the front file to simulate a dangling reference
    (tmp_path / "characters" / cid / "wardrobe" / gid / "refs" / "front.png").unlink()
    with pytest.raises(al.AssetLookupError) as e:
        al.build_pack(root=str(tmp_path), character_ids=[cid], wardrobe=[gid])
    assert any("missing file" in err for err in e.value.errors)


def test_ambiguous_prop_slug(tmp_path):
    _prop(tmp_path, "set-dressing.lantern_01")
    _prop(tmp_path, "wearable.lantern_01")
    with pytest.raises(al.AssetLookupError) as e:
        al.build_pack(root=str(tmp_path), props=["lantern_01"])
    assert any("ambiguous" in err for err in e.value.errors)


# --- no hard-coded absolute paths -------------------------------------------------

def test_no_hardcoded_absolute_paths():
    for name in ("asset_library.py", "asset_lookup.py"):
        p = os.path.join(os.path.dirname(__file__), "..", "tools", name)
        src = open(p, encoding="utf-8").read()
        for needle in ("E:\\", "C:\\", "E:/", "C:/", "/home/", "\\\\FNI"):
            assert needle not in src, f"{name} contains hard-coded absolute path {needle!r}"