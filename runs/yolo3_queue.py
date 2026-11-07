"""YOLO pass 3 — a NEW-SEED take of every chunk that already has one (take 02).

Same chunks, same prompts, same audio, same sheets: the ONLY variable is the seed, so a
take-1 vs take-2 pair isolates what seed variance alone does to cast adherence, framing and
register. (Alex 2026-11-06: "que up another render pass then with new seeds".)

Seeds are deterministic — `seed_for(cid + "|t02")` — and provably different from each chunk's
take-1 seed (`seed_for(cid)`), so the pass is reproducible and re-runnable.

Take 02 means filenames become `<chunk>_audioOnly_t02_00001_.mp4`, so pass 1/2 takes are never
overwritten, and state lives in its own `runs/yolo3_state.json` so their provenance is untouched.

    .venv/Scripts/python.exe runs/yolo3_queue.py --limit 4      # a small first batch
    .venv/Scripts/python.exe runs/yolo3_queue.py                # the whole set
    .venv/Scripts/python.exe runs/yolo3_queue.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"E:/FNI")
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))
from fullrun import seed_for  # noqa: E402  — the same per-chunk seed function the passes use

PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
DRIVER = str(ROOT / "runs" / "build_technicolor_audio_only.py")
STATE2 = ROOT / "runs" / "yolo_state.json"      # passes 1+2
STATE3 = ROOT / "runs" / "yolo3_state.json"     # this pass
TAKE = 2
SALT = "|t02"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save(p: Path, d: dict) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
    tmp.replace(p)


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--limit", type=int, default=0, help="queue at most N chunks this run")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, queue nothing")
    args = ap.parse_args()

    prev = load(STATE2).get("chunks", {})
    have = sorted(cid for cid, v in prev.items() if v.get("queued"))
    st = load(STATE3)
    st.setdefault("chunks", {})

    todo = [c for c in have if not st["chunks"].get(c, {}).get("queued")]
    print("chunks with a take-1: %d | already queued for take-2: %d | to queue: %d"
          % (len(have), len(st["chunks"]), len(todo)))
    if args.limit:
        todo = todo[:args.limit]

    for cid in todo:
        seed = seed_for(cid + SALT)
        t01 = seed_for(cid)
        assert seed != t01, "seed collision for %s" % cid
        cmd = [PY, DRIVER, "--chunk", cid, "--take", str(TAKE), "--seed", str(seed), "--queue"]
        if args.dry_run:
            print("  DRY %s seed %d (t01 was %d)" % (cid, seed, t01))
            continue
        rc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        out = (rc.stdout or "") + (rc.stderr or "")
        last = out.strip().splitlines()[-1][:200] if out.strip() else ""
        if "QUEUED" in out:
            st["chunks"][cid] = {"queued": now(), "seed": seed, "take": TAKE, "note": last}
            print("  %s: %s" % (cid, last), flush=True)
        else:
            st["chunks"][cid] = {"failed": now(), "seed": seed, "take": TAKE, "note": last}
            print("  %s: FAILED %s" % (cid, last), flush=True)
        save(STATE3, st)

    q = sum(1 for c in st["chunks"].values() if "queued" in c)
    f = sum(1 for c in st["chunks"].values() if "failed" in c)
    print("pass 3 state: queued %d, failed %d -> %s" % (q, f, STATE3))


if __name__ == "__main__":
    main()
