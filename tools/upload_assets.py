#!/usr/bin/env python
"""Upload generated character sheets + location plates into a ComfyUI input dir.

Moves the assets produced by gen_char_sheet.py / gen_location_plates.py from
refs/ into the target box's ComfyUI `input/` via POST /upload/image (overwrite=true),
so the restyle/master-plate workflows on that box can LoadImage them by basename.

Usage:
    .venv/Scripts/python.exe tools/upload_assets.py --target 4090    # mh370 localhost:8188
    .venv/Scripts/python.exe tools/upload_assets.py --target 5090    # tombstone Tailscale
    .venv/Scripts/python.exe tools/upload_assets.py --target 4090 --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")

TARGETS = {
    "4090": os.environ.get("FNI_PLATE_COMFY", "http://127.0.0.1:8188").rstrip("/"),
    "5090": os.environ.get("FNI_COMFY", "http://<TOMBSTONE_TS_IP>:8188").rstrip("/"),
}


def collect() -> list[Path]:
    files: list[Path] = []
    # character sheets
    for d in sorted((ROOT / "refs" / "characters").iterdir()):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*_sheet_t*.png")):
            if p.suffix == ".png" and "_graph" not in p.name:
                files.append(p)
    # location plates
    bdir = ROOT / "refs" / "backgrounds"
    if bdir.is_dir():
        for d in sorted(bdir.iterdir()):
            if not d.is_dir():
                continue
            for p in sorted(d.glob("*_plate_t*.png")):
                files.append(p)
    return files


def upload(base: str, path: Path) -> str:
    boundary = "----fniassets"
    data = path.read_bytes()
    fn = path.name
    body = b"".join([
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
         f"filename=\"{fn}\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode(),
        data,
        (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\n"
         f"true\r\n--{boundary}--\r\n").encode(),
    ])
    req = urllib.request.Request(base + "/upload/image", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.loads(r.read().decode())
    return out.get("name") or fn


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--target", choices=list(TARGETS), required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = TARGETS[args.target]
    files = collect()
    print(f"{args.target} @ {base}: {len(files)} assets to upload", flush=True)
    n = 0
    for p in files:
        if args.dry_run:
            print(f"  [dry] {p.name}")
            n += 1
            continue
        name = upload(base, p)
        print(f"  uploaded {p.name} -> {name} ({p.stat().st_size} bytes)", flush=True)
        n += 1
    print(f"done: {n} uploaded to {args.target}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
