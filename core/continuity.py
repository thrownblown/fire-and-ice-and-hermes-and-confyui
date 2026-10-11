"""Continuity analysis: setup clustering + chain/cut classification.

Alex's observation (2026-10-06): cross-cut scenes (glacier breaking, fights)
alternate between two camera setups A/B/A/B. Chronological chunking asks H3
to morph across hard cuts and regenerates each setup from scratch every time
the camera returns. Fix: cluster shots by camera setup, chain what chains,
and recreate the cuts in the assembly.

Method (SSIM first, per the Gemini exchange — deterministic, no deps beyond
the venv's opencv/numpy; embeddings only if SSIM under-clusters):
  1. Extract each shot's exact first/last frame from the master in one pass.
  2. SETUP similarity: SSIM(first_i, first_j) within a scene, union-find at
     --setup-th (default 0.90) -> setup tags S03-A, S03-B, ...
  3. CHAIN similarity: SSIM(last_i, first_i+1) for adjacent shots ->
     >= --chain-th (default 0.75) = CHAIN (continuous action), else CUT.
  4. Cross-cut pattern: setup-label sequence per scene; flag >=4 alternations
     between two labels.

Outputs:
  stills/boundary/<shot>_first.jpg,_last.jpg   (cache)
  manifests/continuity.jsonl                   (per shot: setup, chain edges)
  reports/continuity.md                        (human report, per scene)

Run: .venv/Scripts/python.exe core/continuity.py [--scenes S02,S03]
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(r"E:/FNI")
MASTER = ROOT / "Fire.And.Ice.1983.1080p.BluRay.x264-[YTS.AM].mp4"
BOUND = ROOT / "stills" / "boundary"
SHOTS = ROOT / "shots.jsonl"
OUT = ROOT / "manifests" / "continuity.jsonl"
REPORT = ROOT / "reports" / "continuity.md"

W = 256  # downscale width for SSIM


def load_shots():
    shots = [json.loads(l) for l in SHOTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    # scene map: fullrun chunks ledger first (covers everything it chunked)
    scene_of = {}
    chunks = ROOT / "fullrun" / "chunks.jsonl"
    if chunks.exists():
        for l in chunks.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                for sid in r.get("shots", []):
                    scene_of[sid] = r["scene"].upper()
    # beat-sheet timecode fallback for shots fullrun skipped (e.g. S10)
    import re
    ranges = []
    bs = ROOT / "docs" / "beat-sheet-1.md"
    if bs.exists():
        for m in re.finditer(r"\|\s*(S\d+)\s*\|[^|]*\|\s*(\d\d:\d\d:\d\d)[–-](\d\d:\d\d:\d\d)\s*\|",
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


def extract_boundaries(shots):
    """One decode pass; grab start_frame and end_frame-1 for every shot."""
    BOUND.mkdir(parents=True, exist_ok=True)
    want = {}  # frame index -> list of (shot_id, which)
    for s in shots:
        want.setdefault(s["start_frame"], []).append((s["shot_id"], "first"))
        want.setdefault(max(s["start_frame"], s["end_frame"] - 1), []).append((s["shot_id"], "last"))
    todo = {f: lst for f, lst in want.items()
            if any(not (BOUND / ("%s_%s.jpg" % (sid.replace(":", "_"), w))).exists()
                   for sid, w in lst)}
    if not todo:
        print("boundary frames cached (%d shots)" % len(shots))
        return
    need = set(todo)
    print("extracting %d boundary frames from master..." % len(need), flush=True)
    import av
    container = av.open(str(MASTER))
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"
    got = 0
    for idx, frame in enumerate(container.decode(stream)):
        if idx in need:
            img = frame.to_ndarray(format="bgr24")
            for sid, w in todo[idx]:
                p = BOUND / ("%s_%s.jpg" % (sid.replace(":", "_"), w))
                cv2.imwrite(str(p), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            got += 1
            if got % 200 == 0:
                print("  frame %d (%d/%d targets)" % (idx, got, len(need)), flush=True)
            if got >= len(need):
                break
    container.close()
    print("extracted %d/%d" % (got, len(need)), flush=True)


def gray_small(path):
    img = cv2.imread(str(path))
    if img is None:
        return None
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h = int(g.shape[0] * W / g.shape[1])
    return cv2.resize(g, (W, h)).astype(np.float32)


def ssim(a, b):
    if a is None or b is None or a.shape != b.shape:
        return 0.0
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a = cv2.GaussianBlur(a, (11, 11), 1.5)
    mu_b = cv2.GaussianBlur(b, (11, 11), 1.5)
    sa = cv2.GaussianBlur(a * a, (11, 11), 1.5) - mu_a * mu_a
    sb = cv2.GaussianBlur(b * b, (11, 11), 1.5) - mu_b * mu_b
    sab = cv2.GaussianBlur(a * b, (11, 11), 1.5) - mu_a * mu_b
    m = ((2 * mu_a * mu_b + C1) * (2 * sab + C2)) / \
        ((mu_a ** 2 + mu_b ** 2 + C1) * (sa + sb + C2))
    return float(m.mean())


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def bpath(sid, w):
    return BOUND / ("%s_%s.jpg" % (sid.replace(":", "_"), w))


def analyze_scene(scene_shots, setup_th, chain_th):
    n = len(scene_shots)
    firsts = {s["shot_id"]: gray_small(bpath(s["shot_id"], "first")) for s in scene_shots}
    lasts = {s["shot_id"]: gray_small(bpath(s["shot_id"], "last")) for s in scene_shots}

    # setup clusters on start frames
    uf = UF()
    pair_ss = {}
    for i in range(n):
        for j in range(i + 1, n):
            a, b_ = scene_shots[i]["shot_id"], scene_shots[j]["shot_id"]
            v = ssim(firsts[a], firsts[b_])
            pair_ss[(a, b_)] = v
            if v >= setup_th:
                uf.union(a, b_)
    groups = defaultdict(list)
    for s in scene_shots:
        groups[uf.find(s["shot_id"])].append(s["shot_id"])
    # stable labels by first appearance order
    label_of, seen = {}, []
    for s in scene_shots:
        r = uf.find(s["shot_id"])
        if r not in seen:
            seen.append(r)
    tags = {r: "%s-%s" % (scene_shots[0]["scene"], chr(65 + k)) for k, r in enumerate(seen)}

    # chain/cut edges between adjacent shots
    edges = []
    for i in range(n - 1):
        a, b_ = scene_shots[i]["shot_id"], scene_shots[i + 1]["shot_id"]
        v = ssim(lasts[a], firsts[b_])
        edges.append({"from": a, "to": b_, "ssim": round(v, 3),
                      "edge": "CHAIN" if v >= chain_th else "CUT"})

    # cross-cut detection on the label sequence
    seq = [tags[uf.find(s["shot_id"])] for s in scene_shots]
    alt = 0
    for k in range(2, len(seq)):
        if seq[k] == seq[k - 2] and seq[k] != seq[k - 1]:
            alt += 1
    return {
        "scene": scene_shots[0]["scene"],
        "shots": n,
        "setups": {tags[r]: g for r, g in groups.items()},
        "seq": seq,
        "edges": edges,
        "alternations": alt,
        "crosscut": alt >= 4,
        "max_pair_ssim": max(pair_ss.values()) if pair_ss else 0.0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default="")
    ap.add_argument("--setup-th", type=float, default=0.42)
    ap.add_argument("--chain-th", type=float, default=0.45)
    args = ap.parse_args()

    shots = load_shots()
    want = set(s.strip().upper() for s in args.scenes.split(",") if s.strip())
    if want:
        shots = [s for s in shots if s["scene"] in want]
    by_scene = defaultdict(list)
    for s in shots:
        by_scene[s["scene"]].append(s)

    extract_boundaries(shots)

    results = []
    for scene in sorted(by_scene, key=lambda x: int(x[1:])):
        r = analyze_scene(by_scene[scene], args.setup_th, args.chain_th)
        results.append(r)
        print("%s: %d shots, %d setups, %d alternations%s" % (
            r["scene"], r["shots"], len(r["setups"]), r["alternations"],
            "  CROSS-CUT" if r["crosscut"] else ""), flush=True)

    with OUT.open("w", encoding="utf-8") as fh:
        for r in results:
            for sid, tag in [(s, t) for t, g in r["setups"].items() for s in g]:
                pass
            fh.write(json.dumps(r) + "\n")

    lines = ["# Continuity analysis (setup-th=%.2f chain-th=%.2f)" % (args.setup_th, args.chain_th), ""]
    for r in sorted(results, key=lambda x: (-x["alternations"], x["scene"])):
        lines.append("## %s — %d shots, %d setups%s" % (
            r["scene"], r["shots"], len(r["setups"]),
            ", CROSS-CUT (%d alternations)" % r["alternations"] if r["crosscut"] else ""))
        lines.append("Sequence: " + " ".join(t.split("-")[1] for t in r["seq"]))
        for tag, g in sorted(r["setups"].items()):
            lines.append("- %s: %s" % (tag, ", ".join(x.split(":")[1] for x in g)))
        chains = [e for e in r["edges"] if e["edge"] == "CHAIN"]
        if chains:
            lines.append("- CHAIN edges: " + ", ".join(
                "%s->%s (%.2f)" % (e["from"].split(":")[1], e["to"].split(":")[1], e["ssim"])
                for e in chains))
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", OUT, "and", REPORT)


if __name__ == "__main__":
    main()
