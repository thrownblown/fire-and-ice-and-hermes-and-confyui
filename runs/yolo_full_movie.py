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
import time
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


GF_TAGS = "http://<GOLDFISHBOWL_TS_IP>:11434/api/tags"
COMFY_5090 = "http://<TOMBSTONE_TS_IP>:8188"
BLOCK_MODEL = "qwen3-vl-32b-heretic:latest"


def preflight() -> list[str]:
    """The pipeline refuses to run misconfigured. Returns a list of problems
    (empty = go). Every check is cheap (<30s total) and each one names a failure
    that ALREADY burned a run once."""
    import urllib.request
    from core.prompt_guards import looks_like_error
    problems = []

    def get(url, timeout=10):
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())

    # 1. the blocking VLM endpoint must be up AND hold the exact model we name
    try:
        models = [m["name"] for m in get(GF_TAGS).get("models", [])]
        if not any(m.startswith(BLOCK_MODEL.split(":")[0]) for m in models):
            problems.append(f"goldfishbowl is up but {BLOCK_MODEL} is not loaded (has: {models[:5]})")
    except Exception as e:
        problems.append(f"goldfishbowl unreachable: {e}")
    # 2. the render rig must be the 5090 (linux), not an accidental localhost
    try:
        stats = get(COMFY_5090 + "/system_stats")
        if stats.get("system", {}).get("os") != "linux":
            problems.append(f"{COMFY_5090} is NOT the 5090 (os={stats.get('system', {}).get('os')})")
    except Exception as e:
        problems.append(f"5090 ComfyUI unreachable: {e}")
    # 3. the blocking ledger must be clean of error strings before we add to it
    bjp = ROOT / "manifests" / "blocking.json"
    if bjp.exists():
        blk = json.loads(bjp.read_text(encoding="utf-8"))
        bad = [k for k, v in blk.items() if not k.startswith("_") and looks_like_error(v)]
        if bad:
            problems.append(f"blocking.json holds {len(bad)} error entries (e.g. {bad[:3]}) — heal it first")
    # 4. regression guard: the blocker command must pin its endpoint (a missing
    #    --endpoint silently falls through to LM Studio and fails soft)
    src = Path(__file__).read_text(encoding="utf-8")
    if '"--endpoint", "goldfishbowl"' not in src:
        problems.append("yolo_full_movie blocker call lost its --endpoint goldfishbowl pin")
    return problems


def tail(out: str, n: int = 10) -> str:
    lines = [l for l in out.strip().splitlines() if l.strip()]
    return "\n  ".join(lines[-n:])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--queue-only", action="store_true", help="skip the blocking phase")
    ap.add_argument("--block-only", action="store_true", help="draft blocking only, never queue")
    ap.add_argument("--loop", action="store_true",
                    help="feeder mode: rescan forever, queueing chunks whose blocking is ready")
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

    problems = preflight()
    if problems:
        print(f"[{now()}] PREFLIGHT FAILED — refusing to run:", flush=True)
        for p in problems:
            print(f"  - {p}", flush=True)
        sys.exit(2)
    print(f"[{now()}] preflight OK", flush=True)

    while True:
        done_all = do_pass(st, scenes, args, usable_blocking, now)
        if not args.loop or done_all:
            break
        print(f"[{now()}] feeder: waiting for more blocking ...", flush=True)
        time.sleep(120)


def do_pass(st, scenes, args, usable_blocking, now) -> bool:
    """One pass over the scenes. Returns True when every scene is blocked and
    every chunk is in a terminal state (queued/skipped) — the feeder loop's
    exit condition."""
    scene_fail_streak = 0
    chunk_fail_streak = 0

    for sn, chunk_ids in sorted(scenes.items()):
        if not args.queue_only and not st["scenes"].get(sn, {}).get("blocked"):
            print(f"[{now()}] {sn}: drafting blocking ({len(chunk_ids)} chunks) ...", flush=True)
            rc, out = run([PY, BLOCKER, "--scene", sn,
                           "--endpoint", "goldfishbowl",
                           "--model", BLOCK_MODEL,
                           "--sys", "literal", "--write"])
            # verify the pass actually produced usable blocking for this scene —
            # rc=0 with an unreachable VLM used to leave a scene "blocked" with
            # error strings. Count REAL entries; unusable => not blocked, retry next run.
            blk = json.loads((ROOT / "manifests" / "blocking.json").read_text(encoding="utf-8")) \
                if (ROOT / "manifests" / "blocking.json").exists() else {}
            usable = sum(1 for cid in chunk_ids if usable_blocking(blk.get(cid)))
            # partial coverage counts: chunks WITH blocking queue now; stragglers
            # stay untracked (visible in the digest), the scene is not re-drafted
            ok = usable > 0
            st["scenes"][sn] = {"blocked": ok, "rc": rc, "usable": usable,
                                "of": len(chunk_ids), "ts": now()}
            save_state(st)
            print(f"[{now()}] {sn}: blocking rc={rc} usable {usable}/{len(chunk_ids)}", flush=True)
            if not ok:
                # FAIL-STOP: never feed chunks from a failed drafting pass into the
                # queue phase — that is how 40 guard-refusals got spammed last run.
                scene_fail_streak += 1
                print(f"[{now()}] {sn}: BLOCKING PASS FAILED — skipping its chunks.\n  {tail(out)}",
                      flush=True)
                if scene_fail_streak >= 2:
                    print(f"[{now()}] CIRCUIT BREAKER: {scene_fail_streak} consecutive failed "
                          f"blocking passes — something systemic is down. ABORTING RUN.", flush=True)
                    sys.exit(3)
                continue
            scene_fail_streak = 0

        if args.block_only:
            continue

        # feeder precheck: a group-scene chunk without usable blocking isn't
        # "failed", it's just not ready — leave it untracked so the feeder
        # picks it up once its blocking lands (avoids guard-refusal spam)
        blk_now = json.loads((ROOT / "manifests" / "blocking.json").read_text(encoding="utf-8")) \
            if (ROOT / "manifests" / "blocking.json").exists() else {}

        for cid in chunk_ids:
            prev = st["chunks"].get(cid, {})
            if prev.get("queued") or prev.get("skipped"):
                continue
            if sn.startswith("G") and not usable_blocking(blk_now.get(cid)):
                continue
            rc, out = run([PY, DRIVER, "--chunk", cid, "--queue"], timeout=600)
            last = out.strip().splitlines()[-1][:200] if out.strip() else ""
            if "QUEUED" in out:
                st["chunks"][cid] = {"queued": now(), "note": last}
                chunk_fail_streak = 0
                print(f"[{now()}] {cid}: {last}", flush=True)
            elif "no sheeted subjects" in out or "no source audio" in out:
                st["chunks"][cid] = {"skipped": now(), "note": last}
                print(f"[{now()}] {cid}: SKIPPED {last}", flush=True)
            else:
                st["chunks"][cid] = {"failed": now(), "rc": rc, "note": last}
                chunk_fail_streak += 1
                print(f"[{now()}] {cid}: FAILED rc={rc}\n  {tail(out)}", flush=True)
                if chunk_fail_streak >= 8:
                    print(f"[{now()}] CIRCUIT BREAKER: {chunk_fail_streak} consecutive queue "
                          f"failures — the render rig or driver is broken. ABORTING RUN.", flush=True)
                    sys.exit(4)
            save_state(st)

    q = sum(1 for c in st["chunks"].values() if "queued" in c)
    s = sum(1 for c in st["chunks"].values() if "skipped" in c)
    f = sum(1 for c in st["chunks"].values() if "failed" in c)
    print(f"[{now()}] DONE — queued {q}, skipped {s}, failed {f}", flush=True)
    # terminal condition for the feeder loop: every scene blocked AND every
    # chunk accounted for (queued/skipped) — failures stay retryable, so they
    # do not count as done
    all_blocked = all(st["scenes"].get(sn, {}).get("blocked") for sn in scenes)
    total_chunks = sum(len(ids) for ids in scenes.values())
    return all_blocked and (q + s >= total_chunks)


if __name__ == "__main__":
    main()
