"""Audit `manifests/character_names.jsonl` — the per-shot name stamp ships straight into prompts.

Method: score each stamped shot's appearance descriptors (hair + clothing from
`character_pass.jsonl`) against every candidate in that chunk's roster, using the SAME scorer the
prompt builder uses (`core.identity_match.py`) — which vetoes on hair colour and sex. Two kinds of
row are written:

  * `disagree`   — descriptors point at a different character than the stamp, both in the roster;
  * `off_roster` — the stamp names a character the chunk's own ledger excludes (the strong case:
    the chunk's subjects come from its dialogue and blocking, so the stamp is contradicting them).

Result on first run (2026-11-05): 289 stamps on 1308 shots, and **2 flags**, both `disagree` and both
judged NOT actionable — they are the scorer's known blind spot, a pale woman with long black hair in
a purple garment (S20-c02 shot 00787 stamped Teegra vs JULIANA; S25-c02 shot 01186 stamped Teegra vs
LARN). The same blind spot is why an earlier, cruder version of this tool reported 12 conflicts: it
called "long white hair, dark robe" (Nekron) JULIANA. Treat this as a tripwire on sex/hair-colour
contradictions, not as a source of truth about identity.

What it DID establish, and the reason it exists: the S03 chunk roster contained a TEEGRA subject that
came from this stamp rather than from the scene's dialogue (mother and son, Juliana/Nekron). Whether
those frames really show Juliana or Teegra is still open — it needs a look at the frames. Arm 5 of
the S03 experiment follows the dialogue and drops TEEGRA.

Writes `manifests/name_stamp_conflicts.jsonl`. Read-only: it never edits the ledger.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))

from core import identity_match as IM  # noqa: E402
import fullrun as F  # noqa: E402

OUT = ROOT / "manifests" / "name_stamp_conflicts.jsonl"


def traits() -> dict[str, str]:
    out: dict[str, str] = {}
    for d in (ROOT / "refs" / "characters").iterdir():
        if not d.is_dir():
            continue
        f = d / "traits.txt"
        if f.exists():
            out[d.name] = f.read_text(encoding="utf-8", errors="replace")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    T = traits()
    pass_recs = {r["shot_id"]: r for r in F.jl(ROOT / "manifests" / "character_pass.jsonl")}
    names = {r["shot_id"]: r for r in F.jl(ROOT / "manifests" / "character_names.jsonl")}
    chunks = F.jl(ROOT / "fullrun" / "chunks.jsonl")
    chunk_of, roster = {}, {}
    for row in chunks:
        # a chunk's own roster: who the ledger says is in this scene (stamped + speaking)
        names_in = []
        for n in (row.get("speakers") or []) + (row.get("stamped_names") or []):
            if n and n not in names_in:
                names_in.append(n)
        for sid in row["shots"]:
            chunk_of[sid] = row["chunk_id"]
            roster.setdefault(row["chunk_id"], set()).update(n for n in names_in if n)

    rows, kinds = [], collections.Counter()
    for sid, rec in sorted(names.items()):
        for i, p in enumerate(rec.get("people") or []):
            stamped = (p or {}).get("name")
            if not stamped:
                continue
            pr = (pass_recs.get(sid, {}).get("people") or [])
            desc, hair, sex = "", None, None
            if i < len(pr):
                d = pr[i]
                desc = f"{d.get('hair','')} {d.get('clothing','')}"
                hair = d.get("hair")
                sex = IM.sex_of(d.get("sex"))
            if not desc.strip():
                continue
            cid = chunk_of.get(sid, "?")
            cands = sorted(roster.get(cid) or set()) or sorted(T)
            guess = IM.assertable(desc, cands, T, hair=hair, sex=sex)
            # case-insensitive: character_names.jsonl is title-case ("Nekron"), traits dirs are upper
            canon = {c.upper(): c for c in (roster.get(cid) or set())} or {c.upper(): c for c in T}
            stamp_canon = canon.get((stamped or "").upper(), stamped)
            kind = None
            if guess and guess != stamp_canon:
                # is the stamped name even in this chunk's roster?
                kind = "off_roster" if stamped.upper() not in canon else "disagree"
            if not kind:
                continue
            kinds[kind] += 1
            rows.append({"shot_id": sid, "chunk_id": cid, "person_index": i, "stamped": stamped,
                         "descriptor_best": guess, "kind": kind, "desc": desc.strip()[:200],
                         "roster": sorted(roster.get(cid) or [])})

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    stamped_total = sum(len([p for p in (r.get("people") or []) if (p or {}).get("name")])
                        for r in names.values())
    print(f"name stamps audited: {stamped_total} on {len(names)} shots -> "
          f"{len(rows)} conflict(s) in {OUT.name}")
    for k, v in kinds.most_common():
        print(f"  {k}: {v}")
    if not a.quiet:
        print("\n  worst (off_roster — the stamp names someone the chunk's own ledger excludes):")
        for r in [r for r in rows if r["kind"] == "off_roster"][:12]:
            print(f"    {r['chunk_id']} {r['shot_id']}  stamped={r['stamped']:<16} "
                  f"descriptor says {r['descriptor_best']:<16} roster={r['roster']}")
        print("\n  by chunk:")
        for cid, n in collections.Counter(r["chunk_id"] for r in rows).most_common(12):
            print(f"    {cid}: {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
