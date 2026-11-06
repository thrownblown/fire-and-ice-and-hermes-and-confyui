# -*- coding: utf-8 -*-
"""Quick A/B: does removing ALL named weapons/held-objects from a description stop
Krea2 from drawing mangled hands? Renders the same char at several seeds with a
weapon-stripped description and reviews each. Cheap, before committing a re-sweep.

    .venv/Scripts/python.exe tools/test_hand_fix.py --char darkwolf --seeds 6
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"

# import the sweep driver's machinery
sys.path.insert(0, str(ROOT / "tools"))
import subhuman_sweep as sw  # noqa: E402
import review_sweep as rs  # noqa: E402  (its VLM id + judge PROMPT)
sys.path.insert(0, str(ROOT))
from core import gf_client as gf  # noqa: E402  — endpoint + token live there

# sentences that NAME a weapon/prop Krea2 will then draw held
STRIP_PATTERNS = [
    r"[^.]*\b(spear|sword|axe|dagger|bow|knife|staff|club|weapon|blade|haft|scabbard|amulet|pendant|totem)[^.]*\.",
]


def strip_weapons(desc):
    for pat in STRIP_PATTERNS:
        desc = re.sub(pat, ".", desc, flags=re.I)
    return re.sub(r"\s+", " ", desc).strip()


def judge(path):
    return gf.chat(rs.VLM, rs.PROMPT, images=[str(path)],
                   temperature=0.0, max_tokens=2048, timeout=300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True)
    ap.add_argument("--seeds", type=int, default=6)
    args = ap.parse_args()

    char = sw.CHARS[args.char]
    rig = char["rig"]
    comfy = sw.RIGS[rig]
    models = sw.rig_models(comfy)
    desc_file = RUN / "descs" / ("%s.txt" % args.char.upper())
    full = desc_file.read_text(encoding="utf-8").strip()
    desc = strip_weapons(full)
    print("desc: %d -> %d chars after weapon-strip" % (len(full), len(desc)))
    print("stripped:", desc[:200], "...")

    outdir = RUN / "output" / args.char / "handtest"
    outdir.mkdir(parents=True, exist_ok=True)
    for i in range(args.seeds):
        g = sw.build_graph({"styles": [], "actor": "none"}, models, desc)
        g[sw.SAMPLER]["inputs"]["seed"] = 555555 + i
        g[sw.SAVE]["inputs"]["filename_prefix"] = "%s_handtest_%d" % (args.char, i)
        out = sw._post(f"{comfy}/prompt", {"prompt": g, "client_id": "fni-hand-%d" % int(time.time())})
        if out.get("node_errors"):
            print("node error", json.dumps(out["node_errors"]))
            continue
        pid = out["prompt_id"]
        sw.render(comfy, g, outdir)  # pulls the png
    # review the batch
    print("\n-- review --")
    for p in sorted(outdir.glob("*.png")):
        try:
            resp = judge(p)
        except Exception as e:  # noqa: BLE001
            resp = "ERR %s" % e
        v = "GOOD" if resp.startswith("VERDICT=GOOD") else "BAD"
        print("%s %s | %s" % (v, p.name, resp.replace("\n", " ")[:80]))


if __name__ == "__main__":
    main()
