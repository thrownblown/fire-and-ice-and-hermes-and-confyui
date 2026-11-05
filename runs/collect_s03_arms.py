# -*- coding: utf-8 -*-
"""Wait for the six S03 dialogue-fix arm renders and pull them next to T0017.

Three arms x two chunks, queued 2026-11-05 with the same seed T0017 used:
    t02 = sheets-only                  (the t02 canon sheets, prompt as T0017)
    t03 = sheets + presence            (per-shot "who is on screen" + real retention span)
    t04 = sheets + presence + 2 subjects (TEEGRA mis-stamp dropped)

Polls the 5090's /history until each appears, pulls via /view into
runs/T0017_s03_technicolor-audio-only/arms/, and prints a summary. Exits when all six are on disk
or after --timeout minutes. Then rebuild the shot-browser data so they show in the Tests tab:
    .venv/Scripts/python.exe tools/build_testruns_data.py
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
COMFY = "http://<TOMBSTONE_TS_IP>:8188"
DEST = ROOT / "runs" / "T0017_s03_technicolor-audio-only" / "arms"
WANT_TAKES = (2, 3, 4, 5)
WANT = [(f"S03-c0{c}_audioOnly_t0{t}_00001_.mp4", t)
        for t in WANT_TAKES for c in (1, 2)]


def api(path: str, timeout: int = 60):
    with urllib.request.urlopen(COMFY + path, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")


def pull(entry) -> int:
    """entry: (filename, take). Returns bytes written, or 1 if it was already on disk.

    Reporting bug fixed 2026-11-05: this used to `return 0` for a file already present, and the
    caller counts only truthy returns — so a second run of the collector reported "2/6" when all six
    were on disk (the four from the first run were seen as misses). Present == done.
    """
    fn, take = entry
    dst = DEST / f"take{take}__{fn}"
    if dst.exists() and dst.stat().st_size > 1000:
        return 1
    try:
        hist = api("/history", timeout=120)
    except Exception as e:  # noqa: BLE001
        print(f"  [history unreachable: {str(e)[:80]}]", flush=True)
        return 0
    for _pid, rec in hist.items():
        for out in (rec.get("outputs") or {}).values():
            for v in (out.get("videos") or out.get("images") or []):
                if v.get("filename") != fn:
                    continue
                url = COMFY + "/view?" + urllib.parse.urlencode(
                    {"filename": fn, "subfolder": v.get("subfolder", ""),
                     "type": v.get("type", "output")})
                DEST.mkdir(parents=True, exist_ok=True)
                data = urllib.request.urlopen(url, timeout=600).read()
                dst.write_bytes(data)
                print(f"  pulled {dst.name} ({len(data)/1e6:.1f} MB)", flush=True)
                return len(data)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=60, help="minutes to wait")
    ap.add_argument("--interval", type=int, default=30, help="seconds between polls")
    args = ap.parse_args()

    deadline = time.time() + args.timeout * 60
    done: set[str] = set()
    while time.time() < deadline:
        for entry in WANT:
            if entry[0] in done:
                continue
            if pull(entry):
                done.add(entry[0])
        if len(done) == len(WANT):
            break
        time.sleep(args.interval)

    print(f"\narms on disk: {len(done)}/{len(WANT)}", flush=True)
    for fn, take in WANT:
        mark = "OK  " if fn in done else "MISS"
        print(f"  {mark} take{take}  {fn}", flush=True)
    if done:
        print("\nrebuild the SPA data with:")
        print("  .venv/Scripts/python.exe tools/build_testruns_data.py")
    return 0 if len(done) == len(WANT) else 1


if __name__ == "__main__":
    raise SystemExit(main())
