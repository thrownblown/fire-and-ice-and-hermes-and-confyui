#!/usr/bin/env python
"""Classify a character's reference images into canonical (film) vs inspiration (our own renders).

Why: `tools/vlm_traits.py` derives a character's consensus traits from every image in
`refs/characters/<NAME>/`, but that directory mixes SOURCE FILM FRAMES with our own generated
material (Krea2 sweeps, ComfyUI runs, the character SHEET itself). Feeding our own generations
into a trait consensus is circular — the sheet would vote for its own costume, which is exactly
the drift we are trying to detect (TEEGRA's sheet says brown, the film says purple).

`vlm_traits.py` already supports the fix: a `ref_tiers.json` in the character dir, where
`inspiration`-tier files are excluded from the consensus. This writes that file from filename
rules so the split is repeatable and visible rather than hand-made each time.

    .venv/Scripts/python.exe tools/classify_char_refs.py --char LARN            # report only
    .venv/Scripts/python.exe tools/classify_char_refs.py --char LARN --write    # write ref_tiers.json

Rules (film first, anything we generated is inspiration):
  canonical   shot_*.jpg / id_<NAME>.* / *_film_frames_contact.jpg  — frames of the 1983 source
  inspiration ComfyUI_*, fni_*, MiniMax_H3_*, qwedit_*, <NAME>_sheet_*, <NAME>_r0*.png,
              *temp*, *.webp  — our own generations or unknown-origin web refs
Anything the rules do not recognise is listed as UNCLASSIFIED and left out of both tiers, so it
neither votes nor silently disappears — look at it by eye and move it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARS = ROOT / "refs" / "characters"
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")

INSPIRATION_PREFIXES = ("comfyui", "fni_", "minimax_h3", "qwedit", "larn_", "temp")
INSPIRATION_TOKENS = ("_temp", "_sheet_", "_r0", "_r1")


def classify(name: str, fn: str) -> str:
    low = fn.lower()
    if low.startswith("shot_") or low.startswith("id_"):
        return "canonical"
    if "film_frames" in low:
        return "canonical"
    if low.endswith(".webp"):
        return "inspiration"          # unknown-origin web ref (e.g. Larn.webp)
    if low.startswith(INSPIRATION_PREFIXES) or any(t in low for t in INSPIRATION_TOKENS):
        return "inspiration"
    if low.startswith(name.lower().replace(" ", "") + "_") or low.startswith(name.lower() + "_"):
        return "inspiration"
    return "UNCLASSIFIED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--lineage", default="")
    args = ap.parse_args()

    cdir = CHARS / args.char
    if not cdir.is_dir():
        raise SystemExit(f"no such character dir: {cdir}")
    imgs = sorted(fn for fn in (p.name for p in cdir.iterdir())
                  if fn.lower().endswith(IMG_EXT))

    buckets: dict[str, list[str]] = {"canonical": [], "inspiration": [], "UNCLASSIFIED": []}
    for fn in imgs:
        buckets[classify(args.char, fn)].append(fn)

    print(f"{args.char}: {len(imgs)} images")
    for k in ("canonical", "inspiration", "UNCLASSIFIED"):
        print(f"  {k:13s} {len(buckets[k])}")
        for fn in buckets[k]:
            print(f"      {fn}")

    if not args.write:
        print("  (report only — pass --write to create ref_tiers.json)")
        return 0

    tiers = {
        "lineage": args.lineage or (
            f"tiered by tools/classify_char_refs.py: canonical = frames of the 1983 source film, "
            f"inspiration = our own generations (excluded from trait consensus; using them would be "
            f"circular). {args.char} has {len(buckets['canonical'])} canonical film frames."),
        "refs": {},
    }
    for fn in buckets["canonical"]:
        tiers["refs"][fn] = {"tier": "canonical"}
    for fn in buckets["inspiration"]:
        tiers["refs"][fn] = {"tier": "inspiration"}
    out = cdir / "ref_tiers.json"
    out.write_text(json.dumps(tiers, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {out}")
    if buckets["UNCLASSIFIED"]:
        print("  NOTE: UNCLASSIFIED files are in neither tier — they will default to canonical "
              "in vlm_traits.py, so decide on them before trusting the consensus:")
        for fn in buckets["UNCLASSIFIED"]:
            print(f"    ? {fn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
