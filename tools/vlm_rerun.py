#!/usr/bin/env python3
"""Re-run the multi-lens VLM pass over one character, several times, varying
seed and temperature. Writes to a SEPARATE ledger so the original consensus
ledger (manifests/vlm_charpass.jsonl) is never polluted.

Each run = every image x every lens, one serial vision call each. Seed and
temperature are forwarded to LM Studio (qwen3-vl-8b). --no-cache forces a
genuine re-query rather than replaying the cached first-pass rows.

    python tools/vlm_rerun.py --char TEEGRA \
        --run temp=0.3,seed=101 --run temp=0.6,seed=202 \
        --run temp=0.9,seed=303 --run temp=1.0,seed=404 \
        --ledger-out manifests/vlm_charpass_teegra_varied.jsonl
"""
import subprocess
import sys
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
RUNNER = os.path.join(ROOT, "tools", "vlm_character_pass.py")


def main(argv):
    args = argv[:]
    char = None
    runs = []  # list of (temp, seed)
    ledger_out = None
    model = None
    limit = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--char":
            char = args[i + 1]; i += 2; continue
        if a == "--run":
            spec = args[i + 1]
            kv = dict(p.split("=") for p in spec.split(","))
            runs.append((float(kv["temp"]), int(kv.get("seed", 0))))
            i += 2; continue
        if a.startswith("--run="):
            spec = a.split("=", 1)[1]
            kv = dict(p.split("=") for p in spec.split(","))
            runs.append((float(kv["temp"]), int(kv.get("seed", 0))))
            i += 1; continue
        if a == "--ledger-out":
            ledger_out = args[i + 1]; i += 2; continue
        if a == "--model":
            model = args[i + 1]; i += 2; continue
        if a == "--limit":
            limit = args[i + 1]; i += 2; continue
        i += 1

    if not char or not runs:
        print("usage: vlm_rerun.py --char CHAR --run temp=..,seed=.. [--run ...] "
              "[--ledger-out PATH] [--model M] [--limit N]", file=sys.stderr)
        return 2

    ledger_out = ledger_out or os.path.join(
        ROOT, "manifests", f"vlm_charpass_{char.lower()}_varied.jsonl")

    print(f"[vlm_rerun] char={char} runs={runs} ledger={ledger_out} "
          f"start={datetime.now().isoformat()}", flush=True)
    for idx, (temp, seed) in enumerate(runs, 1):
        print(f"[vlm_rerun] === run {idx}/{len(runs)} temp={temp} seed={seed} ===", flush=True)
        cmd = [PY, RUNNER, "--char", char, "--no-cache",
               "--temperature", str(temp), "--seed", str(seed),
               "--ledger-out", ledger_out]
        if model:
            cmd += ["--model", model]
        if limit:
            cmd += ["--limit", str(limit)]
        rc = subprocess.call(cmd, cwd=ROOT)
        if rc != 0:
            print(f"[vlm_rerun] run {idx} exited {rc} (failures; continuing)", flush=True)
    print(f"[vlm_rerun] ALL DONE end={datetime.now().isoformat()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))