#!/usr/bin/env python3
"""Setups v2: VLM-labeled camera setups, replacing SSIM-first-frame clustering.

v1 (core/continuity.py) clustered shots by grayscale SSIM between each shot's
FIRST frame only. That merges only near-identical/static frames, so every
dialogue/action scene fragments to ~1 setup per shot (S13 18/18, S19 13/13,
S25 39/38, ...). A recurring camera angle read as a brand-new setup every time
the actor's pose differs — the exact cross-cut failure this was built to fix.

v2: ask the local VLM (qwen3-vl-8b) to label each shot's first frame with a
compact SETUP SIGNATURE -- location, framing, camera angle -- then cluster shots
within a scene on that signature. A recurring angle is the same setup regardless
of pose/motion, which is what SSIM could not express.

Output schema mirrors v1 (manifests/continuity.jsonl) so build_setups_data.py
and every downstream consumer keeps working unchanged.

Run: .venv/Scripts/python.exe core/setups_v2.py [--scenes S02,S03,S06]
"""
import argparse
import base64
import json
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:/FNI")
BOUND = ROOT / "stills" / "boundary"
SHOTS = ROOT / "shots.jsonl"
OUT = ROOT / "manifests" / "continuity_v2.jsonl"
REPORT = ROOT / "reports" / "continuity_v2.md"
CACHE_DIR = ROOT / "runs" / "setups_v2"
CACHE = CACHE_DIR / "captions_32b.json"

ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen25vl32b"

# Retry ladder: on any failed request, retry the SAME shot with different
# settings. Higher temp shakes a stuck sampler loose; more tokens tolerate a
# rambling preamble before the JSON. Last entry is the final resort.
RETRY_SETTINGS = [
    {"temperature": 0.0, "max_tokens": 128},
    {"temperature": 0.1, "max_tokens": 200},
    {"temperature": 0.3, "max_tokens": 200},
    {"temperature": 0.5, "max_tokens": 256},
]

SYSTEM = (
    "You are labeling film stills for camera-setup grouping. Describe only what "
    "is visually present. Never name characters, actors, or performers. Reply "
    "with strict JSON only, no prose, no markdown fences."
)

PROMPT = (
    "This is one camera shot from an animated fantasy film. Identify its camera "
    "setup using these exact fields:\n"
    "  location: a concrete noun phrase for the setting/background "
    "(e.g. glacier crevasse interior, snowy mountain pass, fortress throne room, "
    "forest clearing). Never empty.\n"
    "  framing: one of XWS, WS, FS, MS, MCU, CU, ECU (extreme-wide to extreme-close).\n"
    "  angle: one of eye-level, high-angle, low-angle, over-the-shoulder, POV, aerial.\n"
    "  persons: integer count of people (human or humanoid) in the shot.\n"
    "  creatures: integer count of animals/mounts/monsters.\n"
    "Respond as JSON with exactly those keys: location, framing, angle, persons, "
    "creatures."
)


def load_shots():
    """Reuse v1's shot list + scene mapping."""
    shots = [json.loads(l) for l in SHOTS.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    scene_of = {}
    chunks = ROOT / "fullrun" / "chunks.jsonl"
    if chunks.exists():
        for l in chunks.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            for sid in r.get("shots", []):
                scene_of[sid] = r["scene"].upper()
    import re
    ranges = []
    bs = ROOT / "docs" / "beat-sheet-1.md"
    if bs.exists():
        for m in re.finditer(
                r"\|\s*(S\d+)\s*\|[^|]*\|\s*(\d\d:\d\d:\d\d)[–-](\d\d:\d\d:\d\d)\s*\|",
                bs.read_text(encoding="utf-8")):
            def sec(tc):
                h, mi, s = tc.split(":")
                return int(h) * 3600 + int(mi) * 60 + int(s)
            ranges.append((m.group(1), sec(m.group(2)), sec(m.group(3))))
    for s in shots:
        sc = scene_of.get(s["shot_id"])
        if not sc and ranges:
            mid = (s["start_pts"] + s["end_pts"]) / 2 / 24000
            for name, t0, t1 in ranges:
                if t0 <= mid <= t1 + 2:
                    sc = name
                    break
        s["scene"] = sc or "??"
    return shots


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1), encoding="utf-8")


def bpath(sid, w="first"):
    return BOUND / ("%s_%s.jpg" % (sid.replace(":", "_"), w))


def ask_vlm(sid):
    """One shot -> one label; retries with varied settings on any failure.

    Returns the parsed dict, or None only after every retry setting fails.
    """
    img = base64.b64encode(bpath(sid).read_bytes()).decode()
    last_err = None
    for s in RETRY_SETTINGS:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": "data:image/jpeg;base64," + img}},
                ]},
            ],
            "temperature": s["temperature"],
            "max_tokens": s["max_tokens"],
        }
        req = urllib.request.Request(
            ENDPOINT, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=120))
            txt = r["choices"][0]["message"]["content"]
            # strip any accidental fences
            txt = txt.strip().strip("`")
            if txt.startswith("json"):
                txt = txt[4:].strip()
            return json.loads(txt)
        except Exception as e:
            last_err = e
            # a crash (not a parse miss) needs the slot a beat to recover
            time.sleep(3.0)
    print("  ! %s: GAVE UP after %d tries: %s" % (sid, len(RETRY_SETTINGS), last_err),
          file=sys.stderr)
    return None


def label_shots(shots):
    """Label every shot's first frame, sequencing calls and caching by shot_id."""
    cache = load_cache()
    started = time.time()
    for i, s in enumerate(shots, 1):
        sid = s["shot_id"]
        if sid in cache and isinstance(cache[sid], dict):
            if i % 50 == 0:
                print("  ... %d/%d cached, up to %s (%.0fs)" % (
                    i, len(shots), sid, time.time() - started), flush=True)
            continue
        lab = ask_vlm(sid)
        cache[sid] = lab if lab is not None else {"error": True}
        save_cache(cache)
        if i % 25 == 0:
            print("  %d/%d labeled (%.0fs) last=%s -> %s" % (
                i, len(shots), time.time() - started, sid,
                "ok" if lab is not None else "FAIL"), flush=True)
    return cache


def sig(lab):
    """Cluster key = location + framing + angle (normalized-lower)."""
    return (str(lab.get("location", "???")).strip().lower(),
            str(lab.get("framing", "??")).strip().upper(),
            str(lab.get("angle", "??")).strip().lower())


def analyze_scene(scene, shots, cache):
    n = len(shots)
    groups = defaultdict(list)
    seq = []
    for s in shots:
        lab = cache.get(s["shot_id"])
        key = sig(lab) if isinstance(lab, dict) else ("UNLABELED", "?", "?")
        groups[key].append(s["shot_id"])
        seq.append(key)
    # stable labels by first appearance order
    seen, tags = [], {}
    for k in seq:
        if k not in seen:
            seen.append(k)
    tags = {k: "%s-%s" % (scene, chr(65 + i)) for i, k in enumerate(seen)}
    setups = {tags[k]: sorted(int(x.split(":")[1]) for x in groups[k]) for k in seen}
    # chain/cut still from v1 (unchanged) -- not re-derived here; kept for schema.
    alt = 0
    labeled_seq = [tags[k] for k in seq]
    for k in range(2, len(labeled_seq)):
        if labeled_seq[k] == labeled_seq[k - 2] and labeled_seq[k] != labeled_seq[k - 1]:
            alt += 1
    return {
        "scene": scene,
        "shots": n,
        "setups": setups,
        "seq": labeled_seq,
        "edges": [],  # v2 leaves edges to v1 (SSIM chain/cut is fine); filled later if desired
        "alternations": alt,
        "crosscut": alt >= 4,
        "details": {k: {**cache.get(s["shot_id"], {})}
                    for s in shots if isinstance(cache.get(s["shot_id"]), dict)
                    for k in [tags[sig(cache[s["shot_id"]])]]},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default="", help="comma list e.g. S02,S03,S06; empty = all scenes")
    args = ap.parse_args()

    shots = load_shots()
    want = set(s.strip().upper() for s in args.scenes.split(",") if s.strip())
    if want:
        shots = [s for s in shots if s["scene"] in want]
    by_scene = defaultdict(list)
    for s in shots:
        by_scene[s["scene"]].append(s)

    print("labeling %d shots across %s..." % (len(shots), sorted(by_scene)), flush=True)
    cache = label_shots(shots)
    n_ok = sum(1 for s in shots if isinstance(cache.get(s["shot_id"]), dict))
    print("labeled %d/%d" % (n_ok, len(shots)), flush=True)

    results = []
    for scene in sorted(by_scene, key=lambda x: int(x[1:])):
        r = analyze_scene(scene, by_scene[scene], cache)
        results.append(r)
        print("%s: %d shots -> %d setups%s" % (
            r["scene"], r["shots"], len(r["setups"]),
            "  CROSS-CUT" if r["crosscut"] else ""), flush=True)

    # write full continuity_v2.jsonl only if we ran everything; else write a partial
    if want and len(by_scene) < 40:
        OUT_v2_pilot = CACHE_DIR / ("pilot_%s.jsonl" % "_".join(sorted(by_scene)))
        OUT_v2_pilot.write_text("\n".join(json.dumps(r) for r in results), encoding="utf-8")
        print("wrote pilot ->", OUT_v2_pilot)
    else:
        OUT.write_text("\n".join(json.dumps(r) for r in results), encoding="utf-8")
        print("wrote", OUT)

    for r in sorted(results, key=lambda x: x["scene"]):
        print("\n== %s: %d setups ==" % (r["scene"], len(r["setups"])))
        print("  seq:", " ".join(t.split("-")[1] for t in r["seq"]))
        for tag, nums in sorted(r["setups"].items()):
            print("  %s: %s" % (tag, ",".join("%05d" % n for n in nums)))


if __name__ == "__main__":
    main()