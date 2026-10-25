# -*- coding: utf-8 -*-
"""Review a character's Krea2 sweep grid with goldfishbowl qwen3-vl-32b-heretic.

For each still in runs/subhuman-krea2/output/<char>/, ask the 32B VLM for a
GOOD/BAD verdict + one-line reason, and write a review.jsonl. The 32B is the
real judge (the 8B passes everything). This feeds the H3-scene pick.

    .venv/Scripts/python.exe tools/review_sweep.py --char taro [--limit N]
    .venv/Scripts/python.exe tools/review_sweep.py --all
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
RUN = ROOT / "runs" / "subhuman-krea2"
GF = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"
VLM = "qwen3-vl-32b-heretic:latest"

PROMPT = (
    "This is a generated still of a sword-and-sandals fantasy character at the dawn of the "
    "bronze age. Judge ONLY these things: (1) is the anatomy coherent (no mangled hands, "
    "broken face, fused limbs, extra fingers)? (2) is the costume/weapon plausible fur, hide, "
    "bone, stone, wood, or crude copper? (3) is the framing sensible (subject fully in frame, "
    "not cropped at the neck/chin)? (4) any text/watermark artifacts? "
    "Answer EXACTLY in this format, nothing else:\n"
    "VERDICT=GOOD or BAD\nWHY=<one short clause>"
)


def b64(path, max_side=1024):
    im = Image.open(path).convert("RGB")
    if max(im.size) > max_side:
        r = max_side / max(im.size)
        im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return base64.b64encode(b.getvalue()).decode()


def judge(path):
    body = json.dumps({"model": VLM, "prompt": PROMPT, "images": [b64(path)],
                       "stream": False, "options": {"temperature": 0.0, "num_ctx": 8192}}).encode()
    req = urllib.request.Request(GF, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return (json.load(r).get("response") or "").strip()


def review_char(char):
    outdir = RUN / "output" / char
    pngs = sorted(outdir.glob("*.png"))
    if not pngs:
        print("%s: no pngs" % char)
        return
    review = RUN / ("%s_review.jsonl" % char)
    done = set()
    if review.exists():
        done = {json.loads(l)["file"] for l in review.read_text(encoding="utf-8").splitlines() if l.strip()}
    with review.open("a", encoding="utf-8") as fh:
        for p in pngs:
            if str(p) in done:
                continue
            try:
                resp = judge(p)
            except Exception as e:  # noqa: BLE001
                resp = "ERROR: %s" % e
            verdict = "GOOD" if resp.startswith("VERDICT=GOOD") else "BAD"
            fh.write(json.dumps({"file": str(p), "verdict": verdict, "resp": resp}) + "\n")
            fh.flush()
            print("%-6s %-40s %s" % (verdict, p.name, resp.replace("\n", " | ")[:80]), flush=True)
    rows = [json.loads(l) for l in review.read_text(encoding="utf-8").splitlines() if l.strip()]
    good = [r for r in rows if r["verdict"] == "GOOD"]
    print("== %s: %d/%d GOOD" % (char, len(good), len(rows)))
    return len(good), len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if args.all:
        import glob
        chars = sorted({Path(m).stem.replace("_sweep_manifest", "") for m in glob.glob(str(RUN / "*_sweep_manifest.jsonl"))})
    elif args.char:
        chars = [args.char]
    else:
        ap.error("pass --char or --all")
    summary = {}
    for c in chars:
        summary[c] = review_char(c)
    print("\nSUMMARY (GOOD/total):")
    for c, r in summary.items():
        if r:
            print("  %-12s %d/%d" % (c, r[0], r[1]))


if __name__ == "__main__":
    main()
