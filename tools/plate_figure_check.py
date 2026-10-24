#!/usr/bin/env python
"""Check location plates for embedded humanoid content, with the 32B VLM.

A plate must be free of DECORATIVE humanoid figures, not just live people: wall
paintings, portraits, statues and figure-tapestries get rendered by H3 as extra
foreground people in the video (a bedchamber plate with two painted women produced
phantom "background extras" for a whole clip).

Judges the NEWEST take of each canonical location by default. Exits non-zero if any
plate is dirty, so it can gate a render.

    .venv/Scripts/python.exe tools/plate_figure_check.py                # all canonical
    .venv/Scripts/python.exe tools/plate_figure_check.py --slug jungle  # one
    .venv/Scripts/python.exe tools/plate_figure_check.py --all-dirs     # every dir under refs/backgrounds
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
MODEL = "qwen3-vl-32b-heretic:latest"
OLLAMA = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"

Q = ("Fantasy film location background plate. Does it contain any PEOPLE, human figures, "
     "portraits, statues, silhouettes of people, or humanoid shapes? "
     "Answer YES or NO, then list each briefly. If none say NO and NONE.")


def newest_plate(slug_dir: Path):
    cands = [p for p in slug_dir.glob("*_plate_t*.png") if "graph" not in p.name]
    if not cands:
        return None

    def take(p: Path):
        m = re.search(r"_t(\d+)_", p.name)
        return (int(m.group(1)) if m else 0, p.name)

    return max(cands, key=take)


def ask(path: Path, timeout: int = 240) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((1100, 1100))
    b = io.BytesIO(); im.save(b, "JPEG", quality=85)
    b64 = base64.b64encode(b.getvalue()).decode()
    body = json.dumps({"model": MODEL, "prompt": Q, "images": [b64], "stream": False}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (json.load(r).get("response") or "").strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug")
    ap.add_argument("--all-dirs", action="store_true", help="every dir under refs/backgrounds")
    ap.add_argument("--json-out", default="manifests/plate_figure_check.json")
    args = ap.parse_args()

    bg = ROOT / "refs" / "backgrounds"
    if args.slug:
        dirs = [bg / args.slug]
    elif args.all_dirs:
        dirs = sorted(d for d in bg.iterdir() if d.is_dir())
    else:
        m = json.loads((ROOT / "manifests" / "locations.json").read_text(encoding="utf-8"))
        dirs = [bg / l["slug"] for l in m["canonical_locations"]]

    results = {}
    dirty = []
    for d in dirs:
        if not d.is_dir():
            print(f"[MISSING ] {d.name}: no dir"); dirty.append(d.name); continue
        p = newest_plate(d)
        if p is None:
            print(f"[MISSING ] {d.name}: no plate"); dirty.append(d.name); continue
        try:
            r = ask(p)
        except Exception as e:  # noqa: BLE001
            r = f"ERR {e}"
        verdict = r.upper().lstrip()
        flag = "FIGURES" if verdict.startswith("YES") else "ok" if verdict.startswith("NO") else "?"
        results[d.name] = {"plate": p.name, "verdict": r}
        if flag != "ok":
            dirty.append(d.name)
        print(f"[{flag:8s}] {d.name:26s} {p.name}: {r[:110]}", flush=True)

    out = ROOT / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(dirty)} dirty / {len(dirs)} checked -> {out}")
    if dirty:
        print("DIRTY:", ", ".join(dirty))
    return 1 if dirty else 0


if __name__ == "__main__":
    sys.exit(main())
