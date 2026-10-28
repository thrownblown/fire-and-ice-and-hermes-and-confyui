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

GF = "http://<GOLDFISHBOWL_TS_IP>:11434/api/generate"
TRIAGE_MODEL = "qwen3-vl-8b-abl:latest"        # fast text triage
DIAG_MODEL = "qwen3-coder:30b"                  # deeper code diagnosis
INTERVAL = 180


def ask(model: str, prompt: str, timeout: int = 240) -> str:
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.1}}).encode()
    req = urllib.request.Request(GF, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (json.load(r).get("response") or "").strip()


def orchestrator_alive() -> bool:
    """Win11-safe: wmic is removed on recent builds — use PowerShell CIM."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object {$_.CommandLine -match 'yolo_full_movie'} | "
             "Select-Object -ExpandProperty ProcessId"],
            capture_output=True, text=True, timeout=30)
        return bool(r.stdout.strip())
    except Exception:
        return False


def relaunch() -> int:
    f = LOG.open("a", encoding="utf-8")
    p = subprocess.Popen([PY, str(ORCH)], stdout=f, stderr=subprocess.STDOUT,
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


def poll(once: bool = False):
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

    alive = orchestrator_alive()
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"chunks": {}}
    counts = {k: sum(1 for c in st["chunks"].values() if k in c) for k in ("queued", "skipped", "failed")}
    total = len(st["chunks"])
    # pending work = retryable failures or chunks never seen; queued+skipped are terminal
    pending = counts.get("failed", 0) > 0 or total < 494

    action = "none"
    if not alive and pending:
        pid = relaunch()
        action = f"orchestrator was dead with work pending — relaunched pid {pid}"
        events.append({"failure": "ORCHESTRATOR DEAD", "class": "death", "why": action})

    row = {"ts": now, "orchestrator_alive": alive, "counts": counts, "tracked": total,
           "new_events": events, "action": action}
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
