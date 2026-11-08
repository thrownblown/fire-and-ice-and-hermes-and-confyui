#!/usr/bin/env python
"""Rebuild docs/plate-location-ruling.md — the 12 scenes that have no settled plate.

Generated, never hand-written: the table is read from `manifests/scene_locations.json` (what the
renderer actually attaches plates from) and from `refs/backgrounds/` (what is on disk), so the doc
cannot drift from the pipeline. The decision entry in `tools/build_project_data.py` points at it, so
it appears in the SPA's Decisions tab.

    .venv/Scripts/python.exe tools/build_plate_ruling_doc.py
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

ROOT = Path(r"E:/FNI")
OUT = ROOT / "docs" / "plate-location-ruling.md"
# the six plates that no settled scene claims — they read as made for the action stretches
FREE = ["frozen-landscape", "north-village-plain", "open-sky", "swamp", "wilderness", "ice-peak-cave"]


def tbl(header: list[str], lines: list[str]) -> str:
    return ("| " + " | ".join(header) + " |\n|" + "|".join(["---"] * len(header)) + "|\n"
            + "\n".join(lines) + "\n")


def main() -> int:
    loc = json.loads((ROOT / "manifests" / "scene_locations.json").read_text(encoding="utf-8"))["scenes"]
    rows = [json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    total = len(rows)

    plates = {}
    for d in sorted((ROOT / "refs" / "backgrounds").iterdir()):
        if d.is_dir() and d.name != "_thumbs":
            # images only: the *_plate_*.graph.json sidecars match the same substring and would
            # inflate every count (73 plates read as 108 files that way)
            n = len([p for p in d.iterdir()
                     if "_plate_" in p.name and p.suffix.lower() in (".png", ".jpg", ".jpeg")])
            if n:
                plates[d.name] = n
    claimed: dict[str, list[str]] = collections.defaultdict(list)
    for sc, rec in loc.items():
        if rec.get("slug") and rec.get("status") in ("from beat sheet", "inferred"):
            claimed[rec["slug"]].append(sc)

    undet = {sc: r for sc, r in loc.items() if r.get("status") in ("UNMATCHED", "PROPOSED")}
    g = {sc: r for sc, r in undet.items() if sc.startswith("G")}
    other = {sc: r for sc, r in undet.items() if not sc.startswith("G")}
    settled = sum(1 for r in loc.values() if r.get("status") in ("from beat sheet", "inferred"))
    scope = sum(r["chunks"] for r in loc.values() if r.get("status") in ("from beat sheet", "inferred"))

    L = ["# Plate location ruling — %d scenes\n" % len(undet)]
    L.append("Every chunk attaches one scene plate. **%d of %d scenes resolve already**, from the beat sheet's own\n"
             "\"Canonical location\" column (`manifests/scene_locations.json`); the %d below do not, so they are the\n"
             "only chunks in the next pass that would render with **no plate**. One word per scene is enough.\n"
             % (settled, len(loc), len(undet)))
    L.append("## The nine G scenes — %d chunks\n" % sum(r["chunks"] for r in g.values()))
    L.append("These are the film's **action stretches**. Their ledger `location` field is empty and they do not appear\n"
             "in the beat sheet at all, so there is nothing to match them against — the slugs currently sitting in the\n"
             "table are placeholders and they attach NOTHING until ruled (a guessed plate behind a scene is worse\n"
             "than none). Six plates exist that no other scene claims, and they read as made for these beats:\n")
    L.append(tbl(["plate", "files on disk", "claimed by"],
                 ["| `%s` | %d | — unclaimed |" % (s, plates.get(s, 0)) for s in FREE]))
    L.append("Proposed, for you to confirm or swap (I am not attached to any of these):\n")
    L.append(tbl(["scene", "chunks", "placeholder"],
                 ["| %s | %d | `%s` |" % (sc, r["chunks"], r["slug"] or "-") for sc, r in sorted(g.items())]))
    L.append("\n## The other three — %d chunks\n" % sum(r["chunks"] for r in other.values()))
    L.append("These name a place but not a part of it, so the plates are genuinely ambiguous.\n")
    lines = []
    for sc, r in sorted(other.items()):
        base = "fire-keep" if "fire" in (r.get("from") or "").lower() else "ice-peak"
        cands = [s for s in plates if s.startswith(base)]
        lines.append("| %s | %d | %s | %s |" % (
            sc, r["chunks"], (r.get("from") or "")[:40],
            ", ".join("`%s`%s" % (c, " *(other scenes)*" if claimed.get(c) else " *(unclaimed)*") for c in cands)))
    L.append(tbl(["scene", "chunks", "ledger says", "plates to choose from"], lines))
    L.append("\n## If you would rather not rule now\n")
    L.append("The next pass simply skips all %d (%d chunks) and runs the **%d that resolve** — everything else is\n"
             "ready.\n" % (len(undet), sum(r["chunks"] for r in undet.values()), scope))
    L.append("Images for every plate are in the SPA's **Backgrounds** tab; this table is generated from\n"
             "`manifests/scene_locations.json` and `refs/backgrounds/` by `tools/build_plate_ruling_doc.py`, so it\n"
             "cannot drift from what the renderer actually reads.\n")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print("wrote %s (%d chars)" % (OUT, len("\n".join(L))))
    print("  settled: %d scenes / %d of %d chunks | awaiting a ruling: %d scenes / %d chunks"
          % (settled, scope, total, len(undet), sum(r["chunks"] for r in undet.values())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
