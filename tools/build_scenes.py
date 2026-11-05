# -*- coding: utf-8 -*-
"""Chain the technicolor video path end to end for the Krea2 character sweep:

  winner still  ->  qwen_scene.py (compose the character INTO a scene still)
                ->  review_scenes.py (32B VLM GOOD/BAD on the scene still)
                ->  h3_scene.py (FL2VA I2V from the APPROVED scene still)

This replaces the old pick_winners --render path, which fed the bare character
sheet straight to H3 and asked H3 to paint the scene from text. The scene still
gives H3 a real first frame with the character already in place.

    .venv/Scripts/python.exe tools/build_scenes.py --char darkwolf             # compose + review
    .venv/Scripts/python.exe tools/build_scenes.py --all --dry-run
    .venv/Scripts/python.exe tools/build_scenes.py --char darkwolf --render    # fire H3 from GOOD still
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
# scripts in subdirs must put the repo root on sys.path before importing siblings
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RUN = ROOT / "runs" / "subhuman-krea2"
STILLS = RUN / "scenes" / "stills"
REVIEW = RUN / "scenes" / "scene_review.jsonl"
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
QWSCENE = str(ROOT / "tools" / "qwen_scene.py")
H3SCENE = str(ROOT / "tools" / "h3_scene.py")
REVIEWSCENE = str(ROOT / "tools" / "review_scenes.py")

# scene directions live in pick_winners.py (single source of truth)
from tools import pick_winners  # noqa: E402
SCENES = pick_winners.SCENES


def scene_prompt(char):
    scene = SCENES.get(char, "before a ring of standing stones under ritual firelight")
    return ("Place the character exactly as in the reference photo into this scene: %s. "
            "Keep the character's face, hair and costume unchanged. Full body, mid shot. "
            "No metal of any kind, no weapon drawn in the hand. Keep both hands fully visible "
            "with distinct fingers — nothing covering the hands." % scene)


def best_winner(char):
    w = pick_winners.winners(char)
    if not w:
        return None
    clean = [x for x in w if "clean" in x["why"].lower()]
    return (clean or w)[0]


def char_scene_still(char):
    pfx = "scene_%s_qw" % char
    hits = sorted(STILLS.glob(pfx + "_*.png"))
    return hits[-1] if hits else None


def approved_still(char):
    if not REVIEW.exists():
        return None
    good = [json.loads(l)["file"] for l in REVIEW.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l).get("verdict") == "GOOD"]
    pfx = "scene_%s_qw" % char
    for f in good:
        if Path(f).name.startswith(pfx):
            return Path(f)
    return None


def compose(char, seed, dry, force):
    best = best_winner(char)
    if not best:
        print("%-12s no GOOD still — skip" % char)
        return None
    existing = char_scene_still(char)
    if existing and not force:
        print("%-12s already has scene still %s" % (char, existing.name))
        return existing
    prefix = "scene_%s_qw" % char
    cmd = [PY, QWSCENE, "--base", best["file"], "--prompt", scene_prompt(char),
           "--char", char, "--prefix", prefix, "--seed", str(seed),
           "--width", "768", "--height", "1368"]  # portrait 9:16 to match H3 downstream (T0023)
    if dry:
        print("%-12s [DRY] qwen_scene %s" % (char, best["file"]))
        return None
    print("%-12s composing scene still from %s ..." % (char, Path(best["file"]).name))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("    qwen_scene FAILED:\n%s\n%s" % (r.stdout[-2000:], r.stderr[-2000:]))
        return None
    p = STILLS / (prefix + "_00001_.png")
    return p if p.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--char", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--render", action="store_true", help="fire h3_scene from the approved scene still")
    ap.add_argument("--review", action="store_true", help="run review_scenes.py after composing")
    ap.add_argument("--force", action="store_true", help="re-compose even if a scene still exists")
    ap.add_argument("--seed-base", type=int, default=1000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.all:
        chars = sorted({p.stem.replace("_review", "") for p in RUN.glob("*_review.jsonl")})
    elif args.char:
        chars = [args.char]
    else:
        ap.error("pass --char or --all")

    for i, c in enumerate(chars):
        still = compose(c, args.seed_base + i, args.dry_run, args.force)
        if args.render:
            approved = approved_still(c)
            if not approved:
                print("%-12s no approved (GOOD) scene still — run --review first" % c)
                continue
            scene = SCENES.get(c, "before a ring of standing stones under ritual firelight")
            if args.dry_run:
                print("%-12s [DRY] h3_scene --still %s --scene %r" % (c, approved.name, scene))
                continue
            print("%-12s firing H3 scene from %s ..." % (c, approved.name))
            subprocess.run([PY, H3SCENE, "--still", str(approved), "--char", c, "--scene", scene],
                           capture_output=True, text=True)

    if args.review and not args.dry_run:
        print("\nreviewing scene stills ...")
        subprocess.run([PY, REVIEWSCENE], capture_output=True, text=True)
    print("\ndone")


if __name__ == "__main__":
    main()
