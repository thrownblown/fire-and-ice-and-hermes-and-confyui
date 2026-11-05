"""QC a take set — black / frozen / silence, resumable.

Why this exists: `fullrun/qc-results.jsonl` (494 rows, all PASS, 2026-10-06) covers ONLY the
FL2VA baseline (`*_full_t01.mp4`). The 256 audio-led takes queued 2026-10-28
(`*_audioOnly_t01_*.mp4`, pulled into `runs/yolo_output/`) have NO QC rows at all — that is
board row 2 in the coordination repo ("QC the audio-led takes (256 chunks)").

Thresholds are the absorbed-prod-lessons ones, NOT reinvented here — they are imported from
`core/overnight_qc.py` so the two ledgers stay comparable:
    FAIL-black   blackdetect time  >= 30% of duration
    FAIL-frozen  freezedetect time >= 40% of duration
    WARN-silent  chunk has dialogue and mean_volume < -45 dB (info only — audio plans A/C
                 replace H3 audio anyway)

    .venv/Scripts/python.exe tools/qc_audioled.py --limit 2            # smoke
    .venv/Scripts/python.exe tools/qc_audioled.py                      # the audio-led set
    .venv/Scripts/python.exe tools/qc_audioled.py \\
        --dir fullrun/output --glob '*_full_t01.mp4' --ledger fullrun/qc-results.recheck.jsonl

Writes one JSON row per take, appended as it goes; takes already in the ledger are skipped, so
re-running continues instead of restarting.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# pipeline/ BEFORE ROOT: `import fullrun` must resolve to pipeline/fullrun.py, never the
# fullrun/ output dir (reorg 2026-10-18); core/overnight_qc.py imports it at module level.
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))

from core.overnight_qc import qc_video  # noqa: E402  (shared thresholds, one implementation)

OUT_DIR = ROOT / "runs" / "yolo_output"
LEDGER = ROOT / "runs" / "yolo_qc.jsonl"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"

def chunk_rows() -> dict:
    rows = {}
    if CHUNKS.exists():
        with CHUNKS.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    rows[r.get("chunk_id") or r.get("id")] = r
    return rows


def done_files(ledger: Path) -> set:
    seen = set()
    if ledger.exists():
        with ledger.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        seen.add(json.loads(line)["file"])
                    except Exception:
                        pass
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="QC at most N takes, then stop (smoke)")
    ap.add_argument("--dir", default=str(OUT_DIR), help="directory holding the takes")
    ap.add_argument("--glob", default="*_audioOnly_t*.mp4", help="take filename pattern")
    ap.add_argument("--ledger", default=str(LEDGER), help="where rows are appended")
    args = ap.parse_args()

    out_dir, ledger = Path(args.dir), Path(args.ledger)
    takes = sorted(out_dir.glob(args.glob))
    if not takes:
        print(f"no takes matching {args.glob} under {out_dir}", file=sys.stderr)
        return 1
    chunks = chunk_rows()
    seen = done_files(ledger)
    todo = [p for p in takes if p.name not in seen]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(takes)} takes in {out_dir}, {len(seen)} already QC'd, {len(todo)} to do", flush=True)

    counts: dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0, "ERROR": 0}
    t0 = time.time()
    with ledger.open("a", encoding="utf-8") as fh:
        for n, path in enumerate(todo, 1):
            cid = re.split(r"_(?:audioOnly|full)_", path.name)[0]
            row = chunks.get(cid, {})
            has_dialogue = bool(row.get("speakers"))
            try:
                r = qc_video(path, has_dialogue)
            except Exception as e:  # noqa: BLE001
                r = {"file": path.name, "verdict": "ERROR", "detail": str(e)[:200]}
            r["chunk_id"] = cid
            r["dialogue"] = has_dialogue
            r["qc_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            v = r["verdict"]
            counts["PASS" if v == "PASS" else
                   "ERROR" if v == "ERROR" else
                   "FAIL" if v.startswith("FAIL") else "WARN"] += 1
            if v != "PASS":
                print(f"  [{n}/{len(todo)}] {cid} {v} {r.get('detail','')}", flush=True)
            elif n % 20 == 0:
                print(f"  ... {n}/{len(todo)} ({(time.time()-t0)/n:.1f}s per take)", flush=True)

    print("QC:", counts, f"in {time.time()-t0:.0f}s -> {ledger}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
