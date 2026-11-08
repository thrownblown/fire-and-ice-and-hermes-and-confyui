"""Queue a render pass — one take of many chunks, with state so it is resumable.

Defaults reproduce the original behaviour (take 02 of every chunk that has a take 01, new salt).
The flags exist because a pass has to be able to isolate ONE variable:

  --take 03 --all                    every chunk in the ledger, fresh new-seed take
  --take 03 --all --reuse-t02-seed   use the take-02 seed wherever one exists, so a change to the
                                     PROMPT or the PLATE is the only difference against a take we
                                     already rendered — no seed variance mixed into the comparison

Seeds are deterministic (`seed_for(cid + salt)`), so any pass is reproducible and re-runnable.

    .venv/Scripts/python.exe runs/yolo3_queue.py --limit 4                  # small first batch
    .venv/Scripts/python.exe runs/yolo3_queue.py --take 03 --all --reuse-t02-seed
    .venv/Scripts/python.exe runs/yolo3_queue.py --take 03 --all --dry-run
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
    ap.add_argument("--take", type=int, default=TAKE, help="take number (filename suffix)")
    ap.add_argument("--salt", default="", help="seed salt; default is |t<take padded to 2>")
    ap.add_argument("--all", action="store_true",
                    help="every chunk in the ledger, not only chunks that already have a take 01")
    ap.add_argument("--reuse-t02-seed", action="store_true",
                    help="where a take-02 seed exists, reuse it so prompt/plate is the only variable")
    ap.add_argument("--plated-only", action="store_true",
                    help="only chunks whose scene resolves to a settled plate")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, queue nothing")
    args = ap.parse_args()

    take = args.take
    salt = args.salt or ("|t%02d" % take)
    # state per take, so passes never overwrite each other's record. yolo3_state.json is the LEGACY
    # name for the take-02 pass — take 03 must not land in it, or its 256 records would read as
    # "already queued" and this pass would silently skip two thirds of the film.
    state_path = ROOT / "runs" / ("yolo3_state.json" if take == 2
                                  else "yolo_t%02d_state.json" % take)

    prev = load(STATE2).get("chunks", {})
    st2 = load(STATE3).get("chunks", {})          # take-02 seeds, for --reuse-t02-seed
    st = load(state_path)
    st.setdefault("chunks", {})

    if args.all:
        rows = [json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
                if l.strip()]
        have = [r["chunk_id"] for r in rows]
    else:
        have = sorted(cid for cid, v in prev.items() if v.get("queued"))

    if args.plated_only:
        sys.path.insert(0, str(ROOT / "runs"))
        import build_technicolor_audio_only as B
        scene_of = {r["chunk_id"]: r["scene"] for r in
                    (json.loads(l) for l in (ROOT / "fullrun" / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
        have = [c for c in have if B.has_plate(scene_of.get(c, ""))]

    todo = [c for c in have if not st["chunks"].get(c, {}).get("queued")]
    reused = sum(1 for c in todo if args.reuse_t02_seed and st2.get(c, {}).get("seed"))
    print("take %02d | salt %s | candidates: %d | already queued: %d | to queue: %d%s"
          % (take, salt, len(have), len(st["chunks"]), len(todo),
             ("  (%d reusing their take-02 seed)" % reused) if reused else ""))
    if args.limit:
        todo = todo[:args.limit]

    for cid in todo:
        if args.reuse_t02_seed and st2.get(cid, {}).get("seed"):
            seed = st2[cid]["seed"]                 # plate/prompt is the only difference from t02
        else:
            seed = seed_for(cid + salt)
            if seed == seed_for(cid):
                seed += 1                           # never collide with the take-01 seed
        cmd = [PY, DRIVER, "--chunk", cid, "--take", str(take), "--seed", str(seed), "--queue"]
        if args.dry_run:
            print("  DRY %s seed %d" % (cid, seed))
            continue
        rc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        out = (rc.stdout or "") + (rc.stderr or "")
        last = out.strip().splitlines()[-1][:200] if out.strip() else ""
        if "QUEUED" in out:
            st["chunks"][cid] = {"queued": now(), "seed": seed, "take": take, "note": last}
            print("  %s: %s" % (cid, last), flush=True)
        else:
            st["chunks"][cid] = {"failed": now(), "seed": seed, "take": take, "note": last}
            print("  %s: FAILED %s" % (cid, last), flush=True)
        save(state_path, st)

    q = sum(1 for c in st["chunks"].values() if "queued" in c)
    f = sum(1 for c in st["chunks"].values() if "failed" in c)
    print("take %02d state: queued %d, failed %d -> %s" % (take, q, f, state_path))


if __name__ == "__main__":
    main()
