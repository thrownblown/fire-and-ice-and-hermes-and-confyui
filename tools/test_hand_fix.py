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

# sentences that NAME a weapon/prop Krea2 will then draw held
STRIP_PATTERNS = [
    r"[^.]*\b(spear|sword|axe|dagger|bow|knife|staff|club|weapon|blade|haft|scabbard|amulet|pendant|totem)[^.]*\.",
]


def strip_weapons(desc):
    for pat in STRIP_PATTERNS:
        desc = re.sub(pat, ".", desc, flags=re.I)
    return re.sub(r"\s+", " ", desc).strip()


def judge(path):
    import base64
    import io
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((1024, 1024), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    b64 = base64.b64encode(b.getvalue()).decode()
    body = json.dumps({"model": sw.review_sweep.VLM if False else "qwen3-vl-32b-heretic:latest",
                       "prompt": sw.review_sweep.PROMPT, "images": [b64],
                       "stream": False, "options": {"temperature": 0.0, "num_ctx": 8192}}).encode()
    req = urllib.request.Request("http://<GOLDFISHBOWL_TS_IP>:11434/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return (json.load(r).get("response") or "").strip()


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
