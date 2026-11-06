# -*- coding: utf-8 -*-
"""Watch the YOLO full-movie run with a LOCAL small model on goldfishbowl —
triage every failure as it happens, remediate the safe cases, escalate the rest.

Why this exists (Alex, 2026-10-27): "why aren't we looking at the errors with a
smaller model on goldfishbowl? we have so much free compute just sitting there."

Loop (every --interval s):
  1. diff-tail runs/yolo_full_movie.log (new FAILED / CIRCUIT / DONE lines)
  2. read runs/yolo_state.json for the aggregate picture
  3. triage each new failure with qwen3-vl-8b-abl (fast, text-only) into
     benign / transient / guard / novel
  4. remediate SAFE cases only:
       - orchestrator process dead with work pending -> relaunch it
       - everything else -> digest only (no unattended code/config edits)
  5. novel failures get a one-paragraph diagnosis from qwen3-coder:30b against
     the failing driver's source, appended to the digest
  6. digest: runs/yolo_diag/watcher_digest.jsonl (one row per poll) +
     OptMem entry on circuit-breaker / death events only

    .venv/Scripts/python.exe tools/log_watcher.py --once     # single pass (test)
    .venv/Scripts/python.exe tools/log_watcher.py            # loop forever
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(r"E:/FNI")
LOG = ROOT / "runs" / "yolo_full_movie.log"
STATE = ROOT / "runs" / "yolo_state.json"
DIGEST = ROOT / "runs" / "yolo_diag" / "watcher_digest.jsonl"
OFFSET = ROOT / "runs" / "yolo_diag" / "watcher.offset"
ORCH = ROOT / "runs" / "yolo_full_movie.py"
DRIVER_SRC = ROOT / "runs" / "build_technicolor_audio_only.py"
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
COMFY_5090 = "http://<TOMBSTONE_TS_IP>:8188"

sys.path.insert(0, str(ROOT))
from core import gf_client as gf  # noqa: E402  — endpoint + token live there

TRIAGE_MODEL = "qwen3-8b-vision-small"   # goldfishbowl alias (fast triage)
DIAG_MODEL = "qwen3-coder-30b"           # goldfishbowl alias (deeper code diagnosis)
INTERVAL = 180


def ask(model: str, prompt: str, timeout: int = 240) -> str:
    return gf.chat(model, prompt, temperature=0.1, max_tokens=4096, timeout=timeout)


def procs_matching(pattern: str) -> bool:
    """Win11-safe: wmic is removed on recent builds — use PowerShell CIM."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             f"Where-Object {{$_.CommandLine -match '{pattern}'}} | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=30)
        return bool(r.stdout.strip())
    except Exception:
        return False


def relaunch(extra_args: list[str]) -> int:
    f = LOG.open("a", encoding="utf-8")
    p = subprocess.Popen([PY, str(ORCH)] + extra_args, stdout=f, stderr=subprocess.STDOUT,
                         cwd=str(ROOT),
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    return p.pid


def triage(failures: list[str]) -> dict:
    if not failures:
        return {}
    prompt = (
        "You are triaging errors from an automated video-render pipeline. For EACH numbered "
        "failure below, answer with one line: `<n> CLASS one-line-reason` where CLASS is one of "
        "benign (expected skip: no sheets, no audio), guard (a deliberate guardrail refusal, "
        "will retry later), transient (timeout/network, retry will fix), novel (a real bug "
        "needing a code fix).\n\n" +
        "\n".join(f"{i+1}. {f[:400]}" for i, f in enumerate(failures)))
    resp = ask(TRIAGE_MODEL, prompt)
    out = {}
    for line in resp.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) >= 2 and parts[0].rstrip(".").isdigit():
            out[int(parts[0].rstrip("."))] = {"class": parts[1], "why": parts[2] if len(parts) > 2 else ""}
    return out


def diagnose(failure: str) -> str:
    src = DRIVER_SRC.read_text(encoding="utf-8")[-6000:]
    prompt = (
        "A video-render pipeline chunk failed with this output:\n\n" + failure[:800] +
        "\n\nHere is the tail of the driver script that produced it:\n\n" + src +
        "\n\nIn ONE short paragraph: the most likely root cause and the one-line fix. "
        "If it looks like a data problem (missing file, bad ledger row) rather than a code "
        "bug, say so plainly.")
    try:
        return ask(DIAG_MODEL, prompt, timeout=420)
    except Exception as e:
        return f"(diagnosis unavailable: {e})"


LOCK = ROOT / "runs" / "yolo_diag" / "watcher.lock"


def acquire_lock() -> bool:
    """Multiple schedulers (Task Scheduler + Hermes cron) may fire a poll at the
    same time — only one may run. Stale locks (>15 min) are a crashed holder."""
    try:
        if LOCK.exists():
            age = time.time() - LOCK.stat().st_mtime
            if age < 900:
                return False
        LOCK.write_text(str(os.getpid()))
        return True
    except OSError:
        return False


def release_lock():
    try:
        LOCK.unlink(missing_ok=True)
    except OSError:
        pass


def pull_new_renders() -> list[str]:
    """Collect completed audioOnly renders off the 5090 onto E: (its /history
    wipes on reboot — an unpulled render is a lost render)."""
    pulled = []
    try:
        with urllib.request.urlopen(COMFY_5090 + "/history?max_items=200", timeout=20) as r:
            hist = json.loads(r.read().decode())
    except Exception:
        return pulled
    outdir = ROOT / "runs" / "yolo_output"
    outdir.mkdir(exist_ok=True)
    for rec in hist.values():
        for o in (rec.get("outputs") or {}).values():
            for v in o.get("videos", []) + o.get("images", []):
                fn = v.get("filename", "")
                if "audioOnly" not in fn or not fn.endswith(".mp4"):
                    continue
                dest = outdir / fn
                if dest.exists() and dest.stat().st_size > 0:
                    continue
                try:
                    from urllib.parse import quote
                    url = (f"{COMFY_5090}/view?filename={quote(fn)}"
                           f"&subfolder={quote(v.get('subfolder', ''))}"
                           f"&type={v.get('type', 'output')}")
                    with urllib.request.urlopen(url, timeout=300) as rr:
                        dest.write_bytes(rr.read())
                    pulled.append(fn)
                except Exception:
                    pass
    return pulled


def poll(once: bool = False):
    if not acquire_lock():
        print("another watcher holds the lock — skipping poll", flush=True)
        return {}
    try:
        return _poll_inner()
    finally:
        release_lock()


def _poll_inner():
    DIGEST.parent.mkdir(parents=True, exist_ok=True)
    off = int(OFFSET.read_text().strip()) if OFFSET.exists() else 0
    text = LOG.read_text(encoding="utf-8", errors="replace") if LOG.exists() else ""
    new = text[off:]
    OFFSET.write_text(str(len(text)))
    now = datetime.datetime.now().isoformat(timespec="seconds")

    new_failures = [l for l in new.splitlines() if "FAILED" in l or "CIRCUIT BREAKER" in l]
    events = []
    tri = triage(new_failures)
    for i, f in enumerate(new_failures, 1):
        cls = tri.get(i, {}).get("class", "novel")
        ev = {"failure": f[:300], "class": cls, "why": tri.get(i, {}).get("why", "")}
        if cls == "novel":
            ev["diagnosis"] = diagnose(f)
        events.append(ev)

    # two supervised roles: the blocker (drafts blocking scene-by-scene, exits
    # when all scenes are blocked) and the feeder (queue-only loop, keeps the
    # 5090 FIFO fed as blocking lands). A dead role with work left gets relaunched.
    blocker_alive = procs_matching("yolo_full_movie.py --block-only")
    feeder_alive = procs_matching("yolo_full_movie.py --queue-only")
    legacy_alive = (not blocker_alive and not feeder_alive) and procs_matching("yolo_full_movie")
    alive = blocker_alive and feeder_alive

    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"chunks": {}, "scenes": {}}
    counts = {k: sum(1 for c in st["chunks"].values() if k in c) for k in ("queued", "skipped", "failed")}
    total = len(st["chunks"])
    # scenes not yet in state are un-blocked too — count against the ledger total
    try:
        all_scenes = {json.loads(l)["scene"] for l in (ROOT / "fullrun" / "chunks.jsonl")
                      .read_text(encoding="utf-8").splitlines() if l.strip()}
    except Exception:
        all_scenes = set(st.get("scenes", {}))
    blocked = {k for k, v in st.get("scenes", {}).items() if v.get("blocked")}
    scenes_unblocked = len(all_scenes - blocked)
    # pending work = un-blocked scenes, retryable failures, or chunks never seen
    pending_queue = counts.get("failed", 0) > 0 or total < 494

    action = []
    if legacy_alive:
        action.append("legacy single orchestrator still running — leaving it (it does both roles)")
    if not blocker_alive and not legacy_alive and scenes_unblocked > 0:
        pid = relaunch(["--block-only"])
        action.append(f"blocker was dead with {scenes_unblocked} scenes un-blocked — relaunched pid {pid}")
        events.append({"failure": "BLOCKER DEAD", "class": "death", "why": action[-1]})
    if not feeder_alive and not legacy_alive and pending_queue:
        pid = relaunch(["--queue-only", "--loop"])
        action.append(f"feeder was dead with work pending — relaunched pid {pid}")
        events.append({"failure": "FEEDER DEAD", "class": "death", "why": action[-1]})
    action = "; ".join(action) if action else "none"

    pulled = pull_new_renders()
    if pulled:
        print(f"  pulled {len(pulled)} renders off the 5090", flush=True)

    row = {"ts": now, "orchestrator_alive": alive, "counts": counts, "tracked": total,
           "pulled": pulled, "new_events": events, "action": action}
    with DIGEST.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(f"[{now}] alive={alive} counts={counts} new_failures={len(new_failures)} action={action}",
          flush=True)
    for ev in events:
        if ev["class"] in ("novel", "death"):
            print("  !!", ev["failure"][:140], flush=True)
            if "diagnosis" in ev:
                print("     dx:", ev["diagnosis"][:300], flush=True)
    # OptMem only for the loud events (circuit breaker / death), not every poll
    loud = [e for e in events if e["class"] in ("death",) or "CIRCUIT" in e["failure"]]
    if loud:
        subprocess.run([PY, str(ROOT / "core" / "optmem.py"), "add", "--kind", "work",
                        "--text", f"log_watcher: {action}; " +
                                  "; ".join(e["failure"][:120] for e in loud)],
                       capture_output=True)
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=INTERVAL)
    args = ap.parse_args()
    if args.once:
        poll(once=True)
        return
    while True:
        try:
            poll()
        except Exception as e:  # the watcher itself must never die silently
            print(f"[watcher error] {e}", flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
