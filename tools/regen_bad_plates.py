#!/usr/bin/env python
"""Regenerate the 11 VLM-BAD location plates with verbose prompts (take 2, same seed).

One-shot companion to tools/gen_location_plates.py. See manifests/plate_vlm_review.json
and the 32B verdicts for which plates are BAD and why.
"""
import json
import os
import sys

sys.path.insert(0, r"E:/FNI/tools")
import gen_location_plates as G  # noqa: E402

ROOT = r"E:/FNI"
SEED_BASE = 800000000000000

BAD = ["akatar-harbor", "darkwolf-camp", "fire-keep-pool", "fire-keep-ramparts",
       "fire-keep-study", "fire-keep-throne-hall", "open-sky", "painted-map-montage",
       "roliel-hut", "ruined-village", "subhuman-camp"]

m = json.load(open(os.path.join(ROOT, "manifests", "locations.json"), encoding="utf-8"))
locs = {l["slug"]: l for l in m["canonical_locations"]}
idx = {l["slug"]: i for i, l in enumerate(m["canonical_locations"])}

n_ok = 0
for slug in BAD:
    loc = locs[slug]
    seed = SEED_BASE + idx[slug]
    try:
        G.run_one(loc, seed, queue=True, take=2)
        n_ok += 1
    except Exception as e:  # noqa: BLE001
        print(f"[{slug}] FAILED: {e}", flush=True)
print(f"REGEN DONE: {n_ok}/{len(BAD)} ok", flush=True)
