# -*- coding: utf-8 -*-
"""Audit audio-led takes with the 32B VLM, PER TAKE — the "did the fix work?" comparison.

Why: `runs/diag_yolo_renders.py` audited `*_audioOnly_t01_00001_*` at 2026-10-27 19:43 and came
back "15-20 identical brown-leather women" — but the bounded-crowd GROUP_CONSTRAINT landed at
19:57 (`5815306`), i.e. AFTER that audit. Seven of those chunks then got a second take
(`00002`, rendered 23:15-23:33) which nobody ever audited, so "the crowd guard works" has never
been tested. This runs the SAME four questions over both takes of each chunk, so the only thing
that differs between the two rows is the constraint the graph was built with.

    .venv/Scripts/python.exe runs/diag_yolo_takes.py --takes 00001,00002
    .venv/Scripts/python.exe runs/diag_yolo_takes.py --chunks G02-c01 --takes 00002 --limit 1

Model id is resolved from the LIVE `GET /v1/models` (never a hardcoded id), transport is
`core/gf_client.py` (never a second hardcoded urllib POST), and the ledger
`runs/yolo_diag/takecmp.jsonl` is resumable on (chunk, take) and kept separate from the pre-fix
`diag_results.jsonl` so the earlier evidence stays intact.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT))

from core import gf_client  # noqa: E402

RUN_DIR = ROOT / "runs" / "T0016_s05_technicolor-audio-only-ref2va"
OUT_DIR = ROOT / "runs" / "yolo_output"
DIAG = ROOT / "runs" / "yolo_diag"
FRAMES = DIAG / "takecmp_frames"
SCALED = DIAG / "takecmp_scaled"
LEDGER = DIAG / "takecmp.jsonl"

DEFAULT_CHUNKS = ["G02-c01", "G03-c01", "G03-c02", "G03-c03", "G03-c05", "G03-c06", "G03-c07"]

PROMPT = (
    "You are auditing an AI video generation for a film remake.\n"
    "The images are: {labels} (in that order).\n"
    "INTENDED SUBJECTS: {subjects}\n"
    "The last 3 images are frames from the generated video.\n"
    "Answer plainly and specifically:\n"
    "1. How many people appear in the generated frames? Describe each (build, hair, costume).\n"
    "2. Does each person MATCH their reference sheet (face, hair, costume)? Say MATCH or MISMATCH"
    " per subject and why.\n"
    "3. What are the people DOING (blocking)? What is the setting?\n"
    "4. List everything wrong vs the intent: extra people, wrong characters, wrong costume, wrong"
    " register (cartoon vs live-action), garbled anatomy."
)


def pick_model(want: str | None) -> str:
    ids = [m.get("id") for m in gf_client.models() if m.get("id")]
    if want:
        return want
    for pref in ("llama-cpp/qwen3-vl-32b", "qwen3-vl-32b"):
        for i in ids:
            if i.startswith(pref):
                return i
    raise SystemExit(f"no 32B VLM id on goldfishbowl; live ids: {ids}")


def prep_image(src: Path, max_px: int = 1024) -> Path:
    """Downscale to a cached ≤max_px JPEG before it goes over the wire.

    Two reasons, both measured 2026-11-04: the 32B VLM now serves **32,768 tokens** of context
    (goldfishbowl cut it from 106,496 to stop a silent VRAM OOM at load), and an image costs
    context as well as VRAM (~4k tokens for a max-size plate). The character sheets here are
    5 MB PNGs; downscaling keeps a sheet+3-frame call comfortably inside the window and is
    faster to upload.
    """
    out = SCALED / f"{src.stem}_{max_px}.jpg"
    if out.exists() and out.stat().st_size > 0:
        return out
    SCALED.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(src),
                    "-vf", f"scale='min({max_px},iw)':-2", "-q:v", "4", "-y", str(out)], check=True)
    return out


def frames_for(chunk: str, take: str) -> list[Path]:
    """3 frames at 10/50/90% of the take, cached on disk."""
    src = OUT_DIR / f"{chunk}_audioOnly_t01_{take}_.mp4"
    if not src.exists():
        return []
    outs = [FRAMES / f"{chunk}_{take}_f{i}.jpg" for i in (1, 2, 3)]
    if all(o.exists() for o in outs):
        return outs
    FRAMES.mkdir(parents=True, exist_ok=True)
    for pct, o in zip((0.10, 0.50, 0.90), outs):
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
                        "-ss", f"{pct:.3f}", "-i", str(src), "-frames:v", "1",
                        "-vf", "scale=768:-1", "-q:v", "3", "-y", str(o)], check=True)
    return outs


def subjects_for(chunk: str) -> tuple[str, list[str]]:
    p = RUN_DIR / "prompts" / f"{chunk}.txt"
    if not p.exists():
        return "(no prompt on disk)", []
    txt = p.read_text(encoding="utf-8")
    m = re.search(r"subject_definitions:\n(.*?)\n\n", txt, re.S)
    block = m.group(1).strip() if m else "(none found)"
    return block, [s.strip() for s in re.findall(r"<Subject \d+> is ([A-Z ]+?),", block)]


def sheet_for(name: str) -> Path | None:
    hits = sorted((ROOT / "refs" / "characters" / name).glob(f"{name}_sheet_t*.png"))
    return hits[0] if hits else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=",".join(DEFAULT_CHUNKS))
    ap.add_argument("--takes", default="00001,00002")
    ap.add_argument("--model", default=None, help="live 32B id (default: discovered)")
    ap.add_argument("--limit", type=int, default=0, help="audit at most N takes, then stop")
    args = ap.parse_args()

    chunks = [c.strip() for c in args.chunks.split(",") if c.strip()]
    takes = [t.strip() for t in args.takes.split(",") if t.strip()]
    model = pick_model(args.model)

    done = set()
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["chunk"], r["take"]))
    jobs = [(c, t) for c in chunks for t in takes
            if (c, t) not in done
            and (OUT_DIR / f"{c}_audioOnly_t01_{t}_.mp4").exists()]
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"model {model} | {len(jobs)} take(s) to audit, {len(done)} already done", flush=True)

    for chunk, take in jobs:
        frames = frames_for(chunk, take)
        if len(frames) != 3:
            print(f"  {chunk} take {take}: frames missing, skipped", flush=True)
            continue
        subj_block, subjects = subjects_for(chunk)
        imgs, labels = [], []
        for n in subjects:
            sp = sheet_for(n)
            if sp:
                imgs.append(str(prep_image(sp)))
                labels.append(f"REF SHEET for {n}")
            else:
                labels.append(f"(no sheet on disk for {n})")
        imgs += [str(f) for f in frames]
        labels += ["GENERATED frame"] * 3
        prompt = PROMPT.format(labels=", ".join(labels), subjects=subj_block)
        try:
            resp = gf_client.chat(model, prompt, images=imgs, max_tokens=3072)
        except Exception as e:  # noqa: BLE001  — a transport error is NOT a verdict
            print(f"  {chunk} take {take}: VLM ERROR {type(e).__name__}: {str(e)[:200]} "
                  f"(nothing written)", flush=True)
            continue
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"chunk": chunk, "take": take, "model": model,
                                 "subjects": subjects, "verdict": resp},
                                ensure_ascii=False) + "\n")
        head = " ".join(resp.split())[:160]
        print(f"  {chunk} take {take}: {len(resp)} chars | {head}", flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
