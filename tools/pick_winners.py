# -*- coding: utf-8 -*-
"""After the strict review, pick the best GOOD still per character and (optionally)
queue an H3 scene from it. Reads <char>_review.jsonl + <char>_sweep_manifest.jsonl
to resolve tag -> style/actor -> file, then reports the winners.

Scene rendering now goes through the Qwen-Edit scene-setup path (compose the
character INTO a scene still, VLM-review it, then H3 I2V): use
`tools/build_scenes.py --all --render`, not the --render flag here.

    .venv/Scripts/python.exe tools/pick_winners.py            # list winners only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
SCENE = str(ROOT / "tools" / "h3_scene.py")

# a scene direction per character (grounded, no weapon grip)
SCENES = {
    "darkwolf": "stands atop a weathered megalith under a storm sky as green shamanic fire coils around his open hands",
    "taro": "stands before a circle of standing stones as wisps of blue spirit-fire drift between the monoliths",
    "jarol": "sits upon a rough-hewn stone throne before a ritual fire, raising one open hand in command",
    "juliana": "stands before a ring of standing stones, arms slightly raised as pale shamanic light gathers",
    "larn": "stands at the edge of a high cliff, wind moving his hair and hide cloak, one hand resting on a bone-tipped spear strapped to his back",
    "nekron": "stands in a circle of ritual fire, hands open at his sides as dark shamanic energy coils upward",
    "otwa": "stands before a great stone altar, arms crossed, as firelight flickers across his frame",
    "roliel": "stands beside a standing stone, red hair stirring, a faint blue glow rising from an open hand",
    "shaitan": "crouches on a low rock, bright eyes catching the firelight, tail flicking",
    "spirit": "drifts slowly among the standing stones, a translucent form trailing faint pale light",
    "subhuman": "crouches before a fire pit, a stone-headed axe across his back, sniffing the night air",
    "teegra": "stands before a sacred fire, arms loose at her sides, pale light on her face",
    "tutor": "stands with hands clasped before him, a quiet authority, firelight on his plain robes",
    "envoys": "kneels before a circle of stones, hood lowered, one open hand raised",
    "leader": "stands before a ring of megaliths, green shamanic fire coiling around his fists",
    "captain": "stands at the head of a stone ramp, surveying, one hand resting on a stone-headed axe at his hip",
}


def load_review(char):
    p = RUN / ("%s_review.jsonl" % char)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_manifest(char):
    p = RUN / ("%s_sweep_manifest.jsonl" % char)
    if not p.exists():
        return {}
    out = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        out[r["tag"]] = r
    return out


def winners(char):
    rev = [r for r in load_review(char) if r["verdict"] == "GOOD"]
    man = load_manifest(char)
    out = []
    for r in rev:
        fn = Path(r["file"]).name
        # tag is "<char>_<style>_<actor>"; strip the "_0000N_.png" suffix
        tag = fn.rsplit("_0000", 1)[0]
        m = man.get(tag) or man.get(fn.rsplit("_00001_", 1)[0])
        out.append({"file": r["file"], "tag": tag,
                    "style": m.get("style_cfg", "?") if m else "?",
                    "actor": m.get("actor", "?") if m else "?",
                    "why": r["resp"]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--char", default=None)
    args = ap.parse_args()

    chars = [args.char] if args.char else sorted({p.stem.replace("_review", "") for p in RUN.glob("*_review.jsonl")})
    for c in chars:
        w = winners(c)
        if not w:
            print("%-12s no GOOD stills" % c)
            continue
        # pick the first GOOD (they're reviewed in filename order); prefer the
        # one with the shortest 'clean' reason
        clean = [x for x in w if "clean" in x["why"].lower()]
        best = (clean or w)[0]
        print("%-12s %d GOOD -> best %s (%s/%s)" % (c, len(w), Path(best["file"]).name, best["style"], best["actor"]))
        if args.render and best["file"]:
            scene = SCENES.get(c, "stands before a ring of standing stones under ritual firelight")
            print("    queueing scene for", c, "...")
            subprocess.run([PY, SCENE, "--still", best["file"], "--char", c, "--scene", scene],
                           capture_output=True, text=True)
            # print the tail of any error
    print("\ndone")


if __name__ == "__main__":
    main()
