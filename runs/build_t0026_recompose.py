# -*- coding: utf-8 -*-
"""T0026: re-compose the BAD-reviewed scene stills with the doctrine-b prompt
template (docs/qwen-edit-prompting-guides.md), one variable changed: prompt
wording. Same winner stills, same seeds as the original build_scenes pass.

Template b per the Reddit doctrine:
  - identity-preservation clause AFTER the action/framing instruction
  - address the ref by slot: "the person in image 1"
  - bans (metal/weapon/hands) between action and identity

taro (GOOD already) is included as the A/B control: scene_taro_qw (template a)
vs scene_taro_qwb (template b), same seed 1011.

Run after the pass-B renders drain, or alongside (composes queue FIFO behind
them on the 5090). Review at the end; GOOD _qwb stills are picked up by
build_scenes.approved_still (prefix match scene_<char>_qw*) for a follow-up
--render pass.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT))
from tools import build_scenes  # noqa: E402

PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
QW = str(ROOT / "tools" / "qwen_scene.py")
REV = str(ROOT / "tools" / "review_scenes.py")

# original pass used seed_base 1000 + index over sorted(chars)
SEEDS = {"darkwolf": 1000, "envoys": 1001, "jarol": 1002, "juliana": 1003,
         "larn": 1004, "nekron": 1005, "otwa": 1006, "roliel": 1007,
         "shaitan": 1008, "spirit": 1009, "subhuman": 1010, "taro": 1011,
         "teegra": 1012, "tutor": 1013}

# BAD-reviewed chars to re-compose + taro as the A/B control
CHARS = ["envoys", "juliana", "nekron", "roliel", "shaitan", "spirit",
         "teegra", "taro"]


def template_b(scene: str) -> str:
    return ("The person in image 1 stands in this scene: %s. Full body, mid shot. "
            "No metal of any kind, no weapon drawn in the hand. Keep both hands fully "
            "visible with distinct fingers, nothing covering the hands. "
            "Maintain the identity of the person in image 1, face, hair and costume "
            "exactly unchanged." % scene)


def main():
    for c in CHARS:
        best = build_scenes.best_winner(c)
        if not best:
            print("%-10s no winner still, skip" % c, flush=True)
            continue
        scene = build_scenes.SCENES.get(
            c, "before a ring of standing stones under ritual firelight")
        cmd = [PY, QW, "--base", best["file"], "--prompt", template_b(scene),
               "--char", c, "--prefix", "scene_%s_qwb" % c,
               "--seed", str(SEEDS[c]), "--width", "768", "--height", "1368"]
        print("%-10s composing (seed %d) ..." % (c, SEEDS[c]), flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        tail = (r.stdout or "")[-300:]
        if r.returncode != 0:
            print("  FAILED rc=%d\n%s\n%s" % (r.returncode, tail, (r.stderr or "")[-300:]),
                  flush=True)
        else:
            print(" ", tail.strip().splitlines()[-1] if tail.strip() else "ok", flush=True)
    print("reviewing new stills ...", flush=True)
    subprocess.run([PY, REV])
    print("done", flush=True)


if __name__ == "__main__":
    main()
