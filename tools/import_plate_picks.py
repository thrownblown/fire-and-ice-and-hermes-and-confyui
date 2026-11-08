#!/usr/bin/env python
"""Fold Alex's plate picks from an exported SPA bundle into manifests/scene_locations.json.

The Decisions tab's plate chooser (view=decisions&item=plate-locations) offers every plate on disk
per scene and stores the picks in localStorage; "export bundle" writes them as `plate_picks`
({scene: slug}). This turns that export into the thing the renderer actually reads, so a pick made in
the page becomes pipeline truth without a human re-typing it — and then regenerates the ruling doc.

A pick is written with status "ruled" (distinct from "from beat sheet"/"inferred", which are
mechanical matches, and from "PROPOSED", which attaches nothing). Only statuses in
("from beat sheet", "inferred", "ruled") attach a plate, so a ruled scene starts rendering with it
immediately, and `plate_for()` still refuses anything unattended.

    .venv/Scripts/python.exe tools/import_plate_picks.py --bundle ~/Downloads/fni-refs-bundle.json
    .venv/Scripts/python.exe tools/import_plate_picks.py --picks '{"G01": "frozen-landscape"}'
    .venv/Scripts/python.exe tools/import_plate_picks.py --bundle ... --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
LOCATIONS = ROOT / "manifests" / "scene_locations.json"
VALID_STATUS = ("from beat sheet", "inferred", "ruled")


def load_picks(args) -> dict:
    if args.bundle:
        b = json.loads(Path(args.bundle).expanduser().read_text(encoding="utf-8"))
        return b.get("plate_picks") or {}
    if args.picks:
        return json.loads(args.picks)
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--bundle", default="")
    ap.add_argument("--picks", default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    picks = load_picks(args)
    if not picks:
        print("no plate_picks in the input — export the bundle from the Decisions tab "
              "(view=decisions&item=plate-locations), then re-run")
        return 1

    data = json.loads(LOCATIONS.read_text(encoding="utf-8"))
    scenes = data.get("scenes") or {}
    shelves = {p.name for p in (ROOT / "refs" / "backgrounds").iterdir() if p.is_dir()}

    applied, rejected = [], []
    for sc, slug in sorted(picks.items()):
        if sc not in scenes:
            rejected.append("%s: not a scene in the table" % sc)
            continue
        if slug not in shelves:
            rejected.append("%s -> %s: no such plate on disk" % (sc, slug))
            continue
        old = scenes[sc]
        applied.append((sc, slug, old.get("status"), old.get("slug")))
        scenes[sc] = {**old, "slug": slug, "status": "ruled",
                      "from": "Alex, Decisions tab (plate chooser), %s"
                              % datetime.date.today().isoformat()}

    for sc, slug, was, old_slug in applied:
        print("  %-5s %-22s (was %s%s)" % (sc, slug, was, "/%s" % old_slug if old_slug else ""))
    for r in rejected:
        print("  REJECTED %s" % r)

    if args.dry_run:
        print("\ndry run: %d would be ruled, %d rejected — nothing written" % (len(applied), len(rejected)))
        return 0
    if not applied:
        print("\nnothing applied")
        return 1

    LOCATIONS.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\nruled %d scene(s) -> %s" % (len(applied), LOCATIONS))
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_plate_ruling_doc.py")], check=False)

    import importlib
    sys.path.insert(0, str(ROOT / "runs"))
    B = importlib.import_module("build_technicolor_audio_only")
    import json as _j
    rows = [_j.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    scope = [r for r in rows if B.has_plate(r["scene"])]
    print("chunks now in scope for a pass: %d / %d" % (len(scope), len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
