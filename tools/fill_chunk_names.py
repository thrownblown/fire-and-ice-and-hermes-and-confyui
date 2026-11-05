"""Fill the missing per-chunk subject names — the thing that keeps half the film unrendered.

Measured 2026-11-05: of 494 chunks, 238 were skipped by the audio-only builder as "no sheeted
subjects", and **227 of those contain people** per `character_pass` (~33 min of film). Nothing is wrong
with those chunks as pictures; the naming pass simply never put a name on anyone in them, and the
builder derives its subjects from `speakers` + `stamped_names` in the chunk ledger.

How this fills them, without inventing anyone:

  1. the CANDIDATE list for a chunk is its scene's cast — every name that appears as speaker or stamp
     anywhere in the same scene. A scene's cast is global even when individual chunks went unstamped.
  2. only candidates that actually have a sheet on disk are eligible (the builder needs a sheet).
  3. each `character_pass` person record in the chunk's shots is matched to a candidate with
     `core.identity_match` — sex and hair colour are HARD vetoes, and a name is only written when the
     evidence clears MIN_SCORE. A person who matches nothing contributes nothing: a wrong name is worse
     than a missing one, because it silently changes who the prompt says is on screen.
  4. the result is written to a NEW ledger (`fullrun/chunks_named.jsonl`), never over `chunks.jsonl`,
     so the original stays as the record of what the naming pass actually produced. Every added name
     carries its evidence in `manifests/name_fill.jsonl`.

Usage:
  python tools/fill_chunk_names.py --report                 # what it would fill, no files written
  python tools/fill_chunk_names.py                          # write the named ledger + fill ledger
  python tools/fill_chunk_names.py --scene S11 --report
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pipeline"))

from core import identity_match as IM  # noqa: E402
import fullrun as F  # noqa: E402

CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
NAMED = ROOT / "fullrun" / "chunks_named.jsonl"
FILL = ROOT / "manifests" / "name_fill.jsonl"


def traits() -> dict[str, str]:
    out = {}
    for d in (ROOT / "refs" / "characters").iterdir():
        if d.is_dir() and (d / "traits.txt").exists():
            out[d.name] = (d / "traits.txt").read_text(encoding="utf-8", errors="replace")
    return out


def has_sheet(name: str) -> bool:
    d = ROOT / "refs" / "characters" / name
    return d.exists() and bool(sorted(d.glob(f"{name}_sheet_t*.png")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    rows = [json.loads(l) for l in CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.scene:
        rows = [r for r in rows if r["scene"] == a.scene]
    T = traits()
    pass_recs = {r["shot_id"]: r for r in F.jl(ROOT / "manifests" / "character_pass.jsonl")}

    # scene cast = every name the scene already uses anywhere
    all_rows = [json.loads(l) for l in CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()]
    cast: dict[str, list[str]] = collections.defaultdict(list)
    for r in all_rows:
        for n in (r.get("speakers") or []) + (r.get("stamped_names") or []):
            if n and n not in cast[r["scene"]]:
                cast[r["scene"]].append(n)

    out_rows, fills, stats = [], [], collections.Counter()
    for r in rows:
        have = [n for n in (r.get("speakers") or []) + (r.get("stamped_names") or []) if has_sheet(n)]
        if have:
            stats["already named"] += 1
            out_rows.append(r)
            continue
        cands = [c for c in cast.get(r["scene"], []) if has_sheet(c)]
        added, evidence = [], []
        for sid in r["shots"]:
            for p in (pass_recs.get(sid, {}).get("people") or []):
                desc = f"{p.get('hair') or ''} {p.get('clothing') or ''}"
                name = IM.assertable(desc, cands, T, hair=p.get("hair"), sex=IM.sex_of(p.get("sex")))
                if not name:
                    continue
                if name not in added:
                    added.append(name)
                evidence.append({"shot": sid, "name": name,
                                 "desc": desc.strip()[:160],
                                 "sex": p.get("sex"), "hair": p.get("hair"),
                                 "score": IM.match_subject(desc, cands, T, hair=p.get("hair"),
                                                           sex=IM.sex_of(p.get("sex")))[1]})
        if added:
            stats["filled"] += 1
            new = dict(r)
            new["stamped_names"] = sorted(set((r.get("stamped_names") or []) + added))
            new["names_filled_by"] = "tools/fill_chunk_names.py"
            out_rows.append(new)
            fills.append({"chunk_id": r["chunk_id"], "scene": r["scene"], "added": added,
                          "candidates": cands, "evidence": evidence})
        else:
            stats["no confident match"] += 1
            out_rows.append(r)

    print(f"chunks considered: {len(rows)}")
    for k, v in stats.most_common():
        print(f"  {k}: {v}")
    if fills:
        print("\n  fill preview (chunk -> names), with the descriptors that justified each:")
        for f in fills[:8]:
            who = ", ".join(f"{e['name']}({e['score']})" for e in f["evidence"][:4])
            print(f"   {f['chunk_id']:<10} +{f['added']}   evidence: {who}")
        print(f"   ... {len(fills)} chunk(s) fillable in total")

    if a.report:
        print("\n--report: nothing written")
        return 0
    NAMED.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out_rows), encoding="utf-8")
    FILL.write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in fills), encoding="utf-8")
    print(f"\nwrote {NAMED.relative_to(ROOT)} ({len(out_rows)} chunks) and {FILL.relative_to(ROOT)} ({len(fills)} fills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
