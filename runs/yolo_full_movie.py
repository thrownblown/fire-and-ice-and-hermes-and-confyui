# -*- coding: utf-8 -*-
"""YOLO full-movie run: draft blocking for every scene, then queue every chunk
through REF2VA audio-only (runs/build_technicolor_audio_only.py --queue).

Order per scene: vlm_blocking --write (goldfishbowl 32B/literal) FIRST, then
queue that scene's chunks — so blocking always leads renders by one scene, and
the 5090's FIFO queue starts chewing immediately. Resumable: state lives in
runs/yolo_state.json, flushed after every chunk; re-run the script to resume.

Chunks with no sheeted subjects or no source audio are recorded as "skipped"
(the driver itself refuses them). Queue failures are recorded as "failed" and
retried on the next run.

    .venv/Scripts/python.exe runs/yolo_full_movie.py            # full pass
    .venv/Scripts/python.exe runs/yolo_full_movie.py --queue-only   # skip blocking phase
    .venv/Scripts/python.exe runs/yolo_full_movie.py --scene S05    # one scene
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
BLOCKER = str(ROOT / "tools" / "vlm_blocking.py")
DRIVER = str(ROOT / "runs" / "build_technicolor_audio_only.py")
STATE = ROOT / "runs" / "yolo_state.json"
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"scenes": {}, "chunks": {}}


def save_state(st: dict):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
    tmp.replace(STATE)


def run(cmd: list[str], timeout: int | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--queue-only", action="store_true", help="skip the blocking phase")
    ap.add_argument("--scene", default=None, help="one scene only")
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT))
    from core.prompt_guards import usable_blocking  # noqa: E402

    rows = [json.loads(l) for l in CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()]
    scenes: dict[str, list[str]] = {}
    for r in rows:
        scenes.setdefault(r["scene"], []).append(r["chunk_id"])
    if args.scene:
        scenes = {args.scene: scenes[args.scene]}

    st = load_state()
    now = lambda: datetime.datetime.now().isoformat(timespec="seconds")

    for sn, chunk_ids in sorted(scenes.items()):
        if not args.queue_only and not st["scenes"].get(sn, {}).get("blocked"):
            print(f"[{now()}] {sn}: drafting blocking ({len(chunk_ids)} chunks) ...", flush=True)
            rc, out = run([PY, BLOCKER, "--scene", sn,
                           "--model", "qwen3-vl-32b-heretic:latest",
                           "--sys", "literal", "--write"])
            # verify the pass actually produced usable blocking for this scene —
            # rc=0 with an unreachable VLM used to leave a scene "blocked" with
            # error strings. Count REAL entries; unusable => not blocked, retry next run.
            blk = json.loads((ROOT / "manifests" / "blocking.json").read_text(encoding="utf-8")) \
                if (ROOT / "manifests" / "blocking.json").exists() else {}
            usable = sum(1 for cid in chunk_ids if usable_blocking(blk.get(cid)))
            ok = rc == 0 and usable > 0
            st["scenes"][sn] = {"blocked": ok, "rc": rc, "usable": usable,
                                "of": len(chunk_ids), "ts": now()}
            save_state(st)
            print(f"[{now()}] {sn}: blocking rc={rc} usable {usable}/{len(chunk_ids)} :: "
                  f"{out.strip().splitlines()[-1][:160] if out.strip() else ''}",
                  flush=True)

        for cid in chunk_ids:
            prev = st["chunks"].get(cid, {})
            if prev.get("queued") or prev.get("skipped"):
                continue
            rc, out = run([PY, DRIVER, "--chunk", cid, "--queue"], timeout=600)
            last = out.strip().splitlines()[-1][:200] if out.strip() else ""
            if "QUEUED" in out:
                st["chunks"][cid] = {"queued": now(), "note": last}
                print(f"[{now()}] {cid}: {last}", flush=True)
            elif "no sheeted subjects" in out or "no source audio" in out:
                st["chunks"][cid] = {"skipped": now(), "note": last}
                print(f"[{now()}] {cid}: SKIPPED {last}", flush=True)
            else:
                st["chunks"][cid] = {"failed": now(), "rc": rc, "note": last}
                print(f"[{now()}] {cid}: FAILED rc={rc} {last}", flush=True)
            save_state(st)

    q = sum(1 for c in st["chunks"].values() if "queued" in c)
    s = sum(1 for c in st["chunks"].values() if "skipped" in c)
    f = sum(1 for c in st["chunks"].values() if "failed" in c)
    print(f"[{now()}] DONE — queued {q}, skipped {s}, failed {f}", flush=True)


if __name__ == "__main__":
    main()
