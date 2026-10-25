# -*- coding: utf-8 -*-
"""Run a rig's roster through the sweep, one character after another.

    .venv/Scripts/python.exe tools/run_rig.py 4090
    .venv/Scripts/python.exe tools/run_rig.py 5090
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:/FNI")
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
SWEEP = str(ROOT / "tools" / "subhuman_sweep.py")

# characters assigned to each rig (must match CHARS in subhuman_sweep.py)
ROSTER = {
    "4090": ["taro", "darkwolf", "jarol", "tutor", "otwa", "nekron", "envoys", "subhuman"],
    "5090": ["larn", "juliana", "roliel", "teegra", "shaitan", "spirit"],
}

if __name__ == "__main__":
    rig = sys.argv[1] if len(sys.argv) > 1 else "5090"
    for name in ROSTER[rig]:
        print("\n================ %s / %s ================" % (rig, name), flush=True)
        r = subprocess.run([PY, SWEEP, "--char", name, "--rig", rig])
        if r.returncode != 0:
            print("!! %s exited %d -- continuing" % (name, r.returncode), flush=True)
    print("\nRIG %s SWEEP DONE" % rig, flush=True)
