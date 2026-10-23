#!/usr/bin/env python
"""Collect-only pass for gen_refs_batch_4090.py.

Recovers a batch whose downloader died but whose jobs were already POSTed to the
4090's queue (they keep rendering in ComfyUI regardless). Polls /history and
downloads any ch_*/pl_* SaveImage output not already on disk, into the newest
refs-batch dir. Never re-queues.

Fixes the bug in the original driver: it downloaded BOTH SaveImage (type output)
and PreviewImage (type temp, identical duplicate) outputs. Here we take only
type == "output" (or, if the box reports both as "output", match the ch_/pl_
filename prefix and skip ComfyUI_temp_*).

Run:
    .venv/Scripts/python.exe tools/collect_refs_batch.py [--dir renders/4090/refs-batch-XXXX]
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
COMFY = "http://127.0.0.1:8188"

CHARS = 120     # 12 characters x 10
PLATES = 210    # 21 locations x 10
TOTAL = CHARS + PLATES


def _get(path, timeout=60):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.loads(r.read().decode() or "null")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=None)
    ap.add_argument("--timeout-min", type=int, default=180)
    args = ap.parse_args()

    if args.dir:
        dest = Path(args.dir)
    else:
        cands = sorted((ROOT / "renders" / "4090").glob("refs-batch-*"))
        dest = cands[-1]
    (dest / "chars").mkdir(parents=True, exist_ok=True)
    (dest / "plates").mkdir(parents=True, exist_ok=True)

    # basenames already on disk (strip the _NNNNN_.png suffix)
    have = set()
    for sub in ("chars", "plates"):
        for f in (dest / sub).glob("*.png"):
            m = re.match(r"((?:ch|pl)_\S+?)_\d+_\.png$", f.name)
            if m:
                have.add(m.group(1))
            else:
                have.add(f.name)

    print(f"collect -> {dest}  (already have {len(have)} basenames)", flush=True)

    deadline = time.time() + args.timeout_min * 60
    fetched = 0
    while time.time() < deadline:
        h = _get("/history")
        got_this_round = 0
        for pid, rec in h.items():
            for out in (rec.get("outputs") or {}).values():
                for im in out.get("images") or []:
                    fn = im["filename"]
                    if not (fn.startswith("ch_") or fn.startswith("pl_")):
                        continue
                    if fn.startswith("ComfyUI_temp_"):
                        continue
                    if im.get("type") == "temp":
                        continue
                    m = re.match(r"((?:ch|pl)_\S+?)_\d+_\.png$", fn)
                    base = m.group(1) if m else fn
                    if base in have:
                        continue
                    sub = "chars" if fn.startswith("ch_") else "plates"
                    q = urllib.parse.urlencode({"filename": fn,
                                                "subfolder": im.get("subfolder", ""),
                                                "type": im.get("type", "output")})
                    data = urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=300).read()
                    out_path = dest / sub / fn
                    out_path.write_bytes(data)
                    have.add(base)
                    fetched += 1
                    got_this_round += 1
        if got_this_round:
            print(f"  +{got_this_round} this round (total {fetched}); "
                  f"{len(have)} basenames, {CHARS+PLATES} expected", flush=True)
        n_char = sum(1 for b in have if b.startswith("ch_"))
        n_plate = sum(1 for b in have if b.startswith("pl_"))
        if n_char >= CHARS and n_plate >= PLATES:
            print(f"COMPLETE: {n_char} chars + {n_plate} plates", flush=True)
            return 0
        time.sleep(10)

    print(f"TIMEOUT: collected {fetched} files; "
          f"chars={sum(1 for b in have if b.startswith('ch_'))}/{CHARS} "
          f"plates={sum(1 for b in have if b.startswith('pl_'))}/{PLATES}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
