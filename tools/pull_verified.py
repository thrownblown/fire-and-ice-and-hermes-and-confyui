#!/usr/bin/env python
"""Robust pull from the 5090: download + integrity-verify + retry.

Fixes the recurring bug where /view returns 200 while the render host is still
writing the file, yielding a truncated mp4 ("moov atom not found"). We fetch,
ffprobe the result, and retry with backoff until the file is a valid, complete
video.

Usage:
    .venv/Scripts/python.exe tools/pull_verified.py --name S05-c01_audioOnly_t04_00001_.mp4 \
        --dest runs/T0016_.../output/t04 --subfolder video --expect-dur 12.25
    # or a list:
    .venv/Scripts/python.exe tools/pull_verified.py --list files.txt --dest DIR
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

COMFY = "http://<TOMBSTONE_TS_IP>:8188"


def probe_duration(p: Path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                       capture_output=True, text=True)
    s = r.stdout.strip()
    try:
        return float(s)
    except ValueError:
        return None


def pull(name: str, dest: Path, subfolder: str, vtype: str, expect_dur=None,
         tries: int = 12) -> bool:
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / name
    q = urllib.parse.urlencode({"filename": name, "subfolder": subfolder, "type": vtype})
    url = f"{COMFY}/view?{q}"
    for a in range(1, tries + 1):
        # wait for a served file with a non-trivial, stable size
        sizes = []
        data = b""
        for _ in range(20):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    data = r.read()
            except Exception as e:  # noqa: BLE001
                print(f"  [{name}] fetch error ({e}); retry", flush=True)
                time.sleep(15)
                continue
            sizes.append(len(data))
            if len(sizes) >= 2 and sizes[-1] == sizes[-2] and sizes[-1] > 100_000:
                break
            time.sleep(8)
        if not sizes or sizes[-1] < 100_000:
            time.sleep(15)
            continue
        out.write_bytes(data)
        d = probe_duration(out)
        if d is None:
            print(f"  [{name}] attempt {a}: {len(data)}B — corrupt, retry", flush=True)
            time.sleep(20)
            continue
        if expect_dur and abs(d - expect_dur) > 0.6:
            print(f"  [{name}] attempt {a}: dur {d:.2f}s != expected {expect_dur:.2f}s — retry", flush=True)
            time.sleep(20)
            continue
        print(f"  [{name}] OK  {len(data)} bytes, {d:.2f}s", flush=True)
        return True
    print(f"  [{name}] FAILED after {tries} attempts", flush=True)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name")
    ap.add_argument("--list", help="file with one 'name [expect_dur]' per line")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--subfolder", default="video")
    ap.add_argument("--type", default="output")
    ap.add_argument("--expect-dur", type=float)
    args = ap.parse_args()

    dest = Path(args.dest)
    items = []
    if args.list:
        for ln in Path(args.list).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split()
            items.append((parts[0], float(parts[1]) if len(parts) > 1 else None))
    elif args.name:
        items.append((args.name, args.expect_dur))
    else:
        ap.error("pass --name or --list")

    ok = sum(1 for n, d in items if pull(n, dest, args.subfolder, args.type, d))
    print(f"{ok}/{len(items)} pulled OK")
    return 0 if ok == len(items) else 1


if __name__ == "__main__":
    sys.exit(main())
