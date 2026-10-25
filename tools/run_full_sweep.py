# -*- coding: utf-8 -*-
"""Run the full-roster Krea2 LoRA sweep on the 5090, one character after another.

Each character's sweep is resumable (its own <char>_sweep_manifest.jsonl skips
already-done cells). Skips the subhuman family already swept under other names.
VLM descriptions are cached in runs/subhuman-krea2/descs/ (done).

    .venv/Scripts/python.exe tools/run_full_sweep.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
SWEEP = str(ROOT / "tools" / "subhuman_sweep.py")

ROSTER = [
    "darkwolf", "envoys", "jarol", "juliana", "larn", "nekron", "otwa",
    "roliel", "shaitan", "spirit", "subhuman", "teegra", "tutor",
]

if __name__ == "__main__":
    for name in ROSTER:
        print("\n================ %s ================" % name, flush=True)
        r = subprocess.run([PY, SWEEP, "--char", name])
        if r.returncode != 0:
            print("!! %s exited %d -- continuing with next" % (name, r.returncode), flush=True)
    print("\nFULL ROSTER SWEEP DONE", flush=True)
