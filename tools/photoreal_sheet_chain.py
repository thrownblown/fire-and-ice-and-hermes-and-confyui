# -*- coding: utf-8 -*-
"""Photoreal character sheets: the two-stage chain, per character.

Stage 1  Qwen-Image-Edit 2511 (4090) turns the character's film-frame identity still into a
         PHOTOREAL person in canon costume — this is the step that changes the medium.
Stage 2  H3 `gen_char_sheet.py --realism --lora-strength 0.0 --still <stage-1 output>` builds the
         multi-view sheet FROM that photoreal input.

Why the chain and not a prompt: measured 2026-11-05 (TEEGRA, one variable per take, same seed) —
H3 ref2va reproduces its REFERENCE'S MEDIUM. A cel frame + realism wording at LoRA 1.05/0.5/0.0 all
read ILLUSTRATION; a photoreal input + LoRA 1.05 reads MIXED; photoreal input + LoRA OFF reads
PHOTOGRAPH. No wording or LoRA setting rescues a cel input.

    .venv/Scripts/python.exe tools/photoreal_sheet_chain.py --chars NEKRON,ROLIEL --take 10
    .venv/Scripts/python.exe tools/photoreal_sheet_chain.py --all-canon --take 10   # every character with traits.txt

Ledger: manifests/photoreal_sheet_chain.jsonl (one row per stage per character).
"""
from __future__ import annotations

import re

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))

PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
G4090 = "http://127.0.0.1:8188"                      # stills/restyle work runs here
QWEN_OUT = ROOT / "runs" / "subhuman-krea2" / "scenes" / "stills"
LEDGER = ROOT / "manifests" / "photoreal_sheet_chain.jsonl"
CHARS = ROOT / "refs" / "characters"

# the 13 sheets the audio-led batch consumed
BATCH = ["TEEGRA", "LARN", "NEKRON", "TUTOR", "JAROL", "TARO", "DARKWOLF", "ROLIEL",
         "JULIANA", "SPIRIT", "ENVOY", "SUBHUMAN CAPTAIN", "SUBHUMAN"]


def traits(name: str) -> str:
    p = CHARS / name / "traits.txt"
    if not p.exists():
        return ""
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            return " ".join(line.split())
    return ""


def film_frames(name: str) -> list[Path]:
    d = CHARS / name
    out = sorted(list(d.glob("shot_*.jpg")) + list(d.glob("film_shot_*.jpg")))
    return out[:6]


def identity_still(name: str) -> Path | None:
    d = CHARS / name
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = d / f"id_{name}{ext}"
        if p.exists():
            return p
    hits = sorted(d.glob("id_*"))
    return hits[0] if hits else None


def stage1(name: str, seed: int) -> Path | None:
    """Qwen-Image-Edit photorealism pass -> photoreal still."""
    base = identity_still(name)
    if not base:
        print(f"[{name}] no identity still — skipped")
        return None
    canon = traits(name) or name
    prompt = (
        f"Convert the person in image 1 into a PHOTOREALISTIC 35mm film still of a live-action actor "
        f"playing this character, keeping their face shape, hair and costume exactly. Canon: {canon}. "
        f"Natural skin texture with visible pores and fine imperfections, real fabric weave and creasing, "
        f"soft directional daylight, shallow depth of field, subtle film grain. "
        f"NOT an illustration, NOT a painting, NOT a 3D render, no line work, no flat colour fills."
    )
    cmd = [PY, "tools/qwen_scene.py", "--comfy", G4090, "--base", str(base),
           "--char", name, "--prefix", f"photoreal_{name.lower().replace(' ', '_')}_t01",
           "--width", "768", "--height", "1368", "--steps", "4", "--seed", str(seed),
           "--prompt", prompt]
    frames = film_frames(name)
    if frames:
        cmd += ["--ref2", str(frames[0])]
    slug = name.lower().replace(" ", "_")
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    # Discover the output DETERMINISTICALLY. Parsing "<tool> downloaded ... -> <path>" out of stdout
    # looked fine on screen but recorded `error-stage1` while the still sat on disk (2026-11-05):
    # never build a path from another process's prose when the filename is derivable.
    want = QWEN_OUT / f"photoreal_{slug}_t01_00001_.png"
    out = want if want.exists() else None
    if out is None:
        hits = sorted(QWEN_OUT.glob(f"photoreal_{slug}_t01*.png"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        out = hits[0] if hits else None
    if out:
        print(f"[{name}] stage1: OK {out.name}")
    else:
        print(f"[{name}] stage1: FAILED rc={r.returncode} {(r.stderr or '')[-160:]}")
    return out


def stage2(name: str, take: int, still: Path) -> tuple[str, str | None, str]:
    """Queue the H3 sheet render. Returns (action, prompt_id, tail).

    `--queue` means gen_char_sheet.py only QUEUES — it never prints the output filename, so the old
    test (`name_sheet_tNN_00001_.png in stdout`) marked every queued render "FAILED". Measured
    2026-11-05: TEEGRA's sheet was reported error-stage2 while its prompt sat PENDING on the 5090.
    The honest signals are the queued prompt id and, later, the file itself
    (`tools/verify_photoreal_chain.py` resolves ids in the rig's history and pulls the PNG).
    """
    r = subprocess.run([PY, "tools/gen_char_sheet.py", "--char", name, "--take", str(take),
                        "--realism", "--lora-strength", "0.0", "--still", str(still), "--queue"],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=2400)
    out = r.stdout or ""
    tail = out.strip().splitlines()[-1][:140] if out.strip() else ((r.stderr or "")[-140:])
    m = re.search(r"queued prompt_id=([0-9a-f-]{8,})", out)
    if m:
        print(f"[{name}] stage2: QUEUED {m.group(1)[:8]} {tail}")
        return "queued-sheet", m.group(1), tail
    if f"{name}_sheet_t{take:02d}_00001_.png" in out:
        print(f"[{name}] stage2: OK {tail}")
        return "wrote-sheet", None, tail
    print(f"[{name}] stage2: FAILED rc={r.returncode} {tail}")
    return "error-stage2", None, tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", default="", help="comma list")
    ap.add_argument("--all-canon", action="store_true", help="every character that has a traits.txt")
    ap.add_argument("--take", type=int, default=10, help="sheet take number (keeps older sheets)")
    ap.add_argument("--seed-base", type=int, default=700000000000000)
    args = ap.parse_args()

    names = [c.strip() for c in args.chars.split(",") if c.strip()] if args.chars else []
    if args.all_canon:
        names = [c for c in BATCH if traits(c)]
    if not names:
        ap.error("pass --chars A,B or --all-canon")

    rows = []
    def emit(row: dict) -> None:
        """Append immediately — a long batch must not lose its ledger to a kill halfway through."""
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        rows.append(row)

    for i, name in enumerate(names):
        row: dict = {"char": name, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "take": args.take}
        if not traits(name):
            print(f"[{name}] no traits.txt — skipped (no canon to render)")
            emit({**row, "action": "skip-no-canon"}); continue
        still = stage1(name, args.seed_base + i)
        if not still or not still.exists():
            emit({**row, "action": "error-stage1"}); continue
        row["photoreal_still"] = str(still.relative_to(ROOT)).replace("\\", "/")
        action, pid, tail = stage2(name, args.take, still)
        row["action"] = action
        if pid:
            row["prompt_id"] = pid
            row["sheet_expected"] = f"{name}_sheet_t{args.take:02d}_00001_.png"
        if tail:
            row["tail"] = tail
        emit(row)

    print("ledger:", LEDGER)
    print("next: run tools/verify_photoreal_chain.py to resolve queued ids and pull the sheets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
