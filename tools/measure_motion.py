# -*- coding: utf-8 -*-
"""Measure camera motion in the source clips — deterministically, from pixels.

Why this exists: the prompts claimed camera moves ("pushes in with small amplitude at slow speed") on
shots whose ledger row said `static`, and the source is a 1983 cel cartoon whose camera mostly holds.
A vision model cannot settle that question — it will answer confidently either way — so this measures
pixels, and the *agreement across the frame* is what decides:

    camera move  -> every tile of the frame shifts together (high agreement)
    content move -> a few tiles shift, the rest hold (low agreement)

A single global phase correlation is dominated by whatever moves most, so a character crossing frame
reads as camera motion; measuring a 3x3 grid of tiles and taking the median, with agreement as a
second gate, keeps a gesturing character inside a locked-off shot reading as a static camera — which
is what the prompt needs to say.

Output: manifests/shot_motion.jsonl, one row per shot:
    {"shot": "shot:00067", "clip": "shot_00067.mp4", "frames": 8,
     "med_px": 0.41, "agree": 0.89, "frac_w": 0.00107, "verdict": "static"}

    .venv/Scripts/python.exe tools/measure_motion.py --shots shot:00067,shot:00068
    .venv/Scripts/python.exe tools/measure_motion.py --limit 60
    .venv/Scripts/python.exe tools/measure_motion.py                 # all 1308 clips
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CLIPS = ROOT / "clips" / "full"
OUT = ROOT / "manifests" / "shot_motion.jsonl"
SAMPLE_W = 384                     # work resolution
FRAMES = 8                         # samples per clip
GRID = 3                           # 3x3 tiles
STATIC_FRAC = 0.0025               # tile-median shift under 0.25% of width => camera holds
AGREE_MIN = 0.55                   # ...and at least this share of tiles must agree on that shift


def _tiles(g: np.ndarray, n: int = GRID):
    h, w = g.shape
    th, tw = h // n, w // n
    for i in range(n):
        for j in range(n):
            yield g[i * th:(i + 1) * th, j * tw:(j + 1) * tw]


def measure(clip: Path, frames: int = FRAMES) -> dict | None:
    cap = cv2.VideoCapture(str(clip))
    if not cap.isOpened():
        return None
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if n < 3:
        cap.release()
        return None
    imgs = []
    for i in np.linspace(0, n - 1, min(frames, n)).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, fr = cap.read()
        if not ok:
            continue
        h = max(1, int(fr.shape[0] * SAMPLE_W / fr.shape[1]))
        imgs.append(cv2.cvtColor(cv2.resize(fr, (SAMPLE_W, h)), cv2.COLOR_BGR2GRAY).astype(np.float32))
    cap.release()
    if len(imgs) < 3:
        return None

    med_shifts, agrees = [], []
    for a, b in zip(imgs, imgs[1:]):
        mags = []
        for ta, tb in zip(_tiles(a), _tiles(b)):
            if ta.shape[0] < 8 or ta.shape[1] < 8:
                continue
            hann = cv2.createHanningWindow((ta.shape[1], ta.shape[0]), cv2.CV_32F)
            (dx, dy), _ = cv2.phaseCorrelate(ta, tb, hann)
            mags.append(float(np.hypot(dx, dy)))
        if not mags:
            continue
        mags = np.asarray(mags)
        med = float(np.median(mags))
        agrees.append(float(np.mean(np.abs(mags - med) <= max(0.75, 0.35 * med + 0.75))))
        med_shifts.append(med)

    if not med_shifts:
        return None
    med_px = float(np.mean(med_shifts))
    agree = float(np.mean(agrees))
    frac = med_px / SAMPLE_W
    moving = frac >= STATIC_FRAC and agree >= AGREE_MIN
    return {"frames": len(imgs), "med_px": round(med_px, 3), "agree": round(agree, 3),
            "frac_w": round(frac, 5), "verdict": "moving" if moving else "static"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default="", help="comma-separated shot ids")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    if a.shots:
        shots = [s.strip() for s in a.shots.split(",") if s.strip()]
    else:
        shots = [json.loads(l)["shot_id"] for l in
                 (ROOT / "shots.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.limit:
        shots = shots[: a.limit]

    rows, miss, stats = [], 0, {"static": 0, "moving": 0}
    for i, sid in enumerate(shots, 1):
        num = sid.split(":")[-1]
        clip = next(iter(CLIPS.glob(f"*{num}.mp4")), None)
        m = measure(clip) if clip else None
        if m is None:
            miss += 1
            continue
        rows.append({"shot": sid, "clip": clip.name, **m})
        stats[m["verdict"]] += 1
        if i % 25 == 0 or i == len(shots):
            print(f"  {i}/{len(shots)} static={stats['static']} moving={stats['moving']} missing={miss}",
                  flush=True)

    Path(a.out).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="")
    print(f"\nwrote {a.out} — {len(rows)} measured: static {stats['static']}, "
          f"moving {stats['moving']}, missing {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
