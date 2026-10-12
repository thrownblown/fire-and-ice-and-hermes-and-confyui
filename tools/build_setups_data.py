#!/usr/bin/env python3
"""Generate setups-data.js for the shot-browser SPA's "Setups" tab.

Reads manifests/continuity.jsonl (output of core/continuity.py: SSIM
setup clustering per scene) and emits window.SETUPDATA with:
  scenes: [{scene, shots, crosscut, setups: {tag: [shotnum,...]},
            seq: [tag per shot in order],
            edges: [{from,to,ssim,edge}]}]
  shot_setup: {shotnum: tag}   (reverse index for shot pages)

A "setup" = one camera angle shared by 1+ shots in a scene: shots that
cut back and forth (cross-cut) share setups, get prompted together with
one master background plate, then are split apart again at assembly.

Usage: python tools/build_setups_data.py
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "manifests", "continuity.jsonl")
OUT = os.path.join(ROOT, "browser", "setups-data.js")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC,
                    help="input jsonl (default: v1 continuity.jsonl)")
    args = ap.parse_args()

    scenes = []
    shot_setup = {}
    with open(args.src, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            scene = rec["scene"]
            setups = {}
            for tag, ids in rec["setups"].items():
                nums = sorted(re.sub(r"^shot:", "", s) for s in ids)
                setups[tag] = nums
                for n in nums:
                    shot_setup[n] = tag
            scenes.append({
                "scene": scene,
                "shots": rec.get("shots", 0),
                "crosscut": bool(rec.get("crosscut")),
                "alternations": rec.get("alternations", 0),
                "setups": setups,
                "seq": rec.get("seq", []),
                "edges": rec.get("edges", []),
            })
    scenes.sort(key=lambda s: s["scene"])
    data = {"scenes": scenes, "shot_setup": shot_setup}
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("window.SETUPDATA = " + json.dumps(data, separators=(",", ":")) + ";\n")
    multi = sum(1 for s in scenes for t, n in s["setups"].items() if len(n) > 1)
    print("wrote %s: %d scenes, %d setups (%d multi-shot), %d shots indexed"
          % (OUT, len(scenes), sum(len(s["setups"]) for s in scenes), multi,
             len(shot_setup)))


if __name__ == "__main__":
    main()
