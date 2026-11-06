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
sys.path.insert(0, str(ROOT))
from core import gf_client as gf  # noqa: E402  — endpoint + token live there

VLM = "qwen3-32b-vision-large"   # goldfishbowl alias (gf_client.ALIASES)

PROMPT = (
    "This is a generated full-body still of a sword-and-sandals fantasy character at the dawn of "
    "the bronze age. Judge STRICTLY — most AI stills have at least one real flaw, so only mark "
    "GOOD if it is genuinely clean. Look for: (1) GROSS anatomy errors only (a clearly mangled "
    "face, extra limbs, a limb missing or fused into the torso, a hand that is visibly a blob or "
    "has six-plus clearly-separated fingers) — do NOT penalize small, far-away hands you cannot "
    "resolve, they are below the resolution of a full-body shot; (2) costume/weapon "
    "implausibility (anachronistic polished metal armour instead of fur/hide/bone/stone/wood/crude "
    "copper); (3) framing faults (subject cropped at neck/chin, feet cut off, important prop "
    "missing); (4) text, watermark, or signature artifacts; (5) background mush, broken "
    "perspective, or melting geometry. If a real flaw is present, verdict is BAD; if you are "
    "unsure about a tiny detail, prefer GOOD.\n"
    "Answer EXACTLY in this format, nothing else:\n"
    "VERDICT=GOOD or BAD\nWHY=<one short clause naming the specific flaw, or 'clean'>"
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
    return gf.chat(VLM, PROMPT, images=[str(path)], temperature=0.0,
                   max_tokens=2048, timeout=300)


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
