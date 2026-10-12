"""Build per-setup stitched reference sources for ref2va.

Groups the raw shots by camera setup (continuity_v2.jsonl) and emits, per setup:

  - {setup}_plate.jpg   contact-sheet collage of the member shots' first-frame
                        stills (the "master background plate" / shared-look image
                        reference; letterboxed to a grid, never cropped).
  - {setup}_ref.mp4     concat (stream copy, no re-encode) of the member shots'
                        24fps refs under refs/, the <Video 1> reference for ref2va.

Also emits manifests/setups.jsonl — a flattened one-row-per-setup ledger (derived
from continuity_v2.jsonl, the single source of truth) so the render/assembly step
can consume setups without re-deriving them.

Run:
  .venv/Scripts/python.exe tools/build_setup_refs.py --scene S06
  .venv/Scripts/python.exe tools/build_setup_refs.py --all
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(r"E:/FNI")
SRC = ROOT / "manifests" / "continuity_v2.jsonl"
LEDGER = ROOT / "manifests" / "setups.jsonl"
BOUNDARY = ROOT / "stills" / "boundary"
REFS = ROOT / "refs"
OUT = ROOT / "refs" / "setups"

CELL = (320, 180)          # per-cell letterbox target for the plate grid
PLATE_MAX = 8              # cap collage members; bigger setups use every Nth still


def load_setups():
    """Return list of (scene, tag, [shot_nums]) sorted scene,tag."""
    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    out = []
    for r in rows:
        for tag, ids in sorted(r["setups"].items()):
            nums = [int(s.split(":")[1]) for s in ids]
            out.append((r["scene"], tag, nums))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def emit_ledger(setups):
    recs = [{"setup_id": tag, "scene": sc, "tag": tag,
             "shots": [f"shot:{n:05d}" for n in nums],
             "shot_nums": nums, "n_members": len(nums)}
            for sc, tag, nums in setups]
    LEDGER.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    return recs


def letterbox(img: Image.Image, target: tuple[int, int]) -> Image.Image:
    """Scale to fit inside target, pad with black bars (never crop)."""
    tw, th = target
    w, h = img.size
    s = min(tw / w, th / h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (tw, th), (0, 0, 0))
    canvas.paste(img, ((tw - nw) // 2, (th - nh) // 2))
    return canvas


def build_plate(scene, tag, nums):
    """Grid collage of first-stills. Returns path or None for singletons."""
    stills = [BOUNDARY / f"shot_{n:05d}_first.jpg" for n in nums]
    stills = [s for s in stills if s.exists()]
    if not stills:
        return None
    if len(stills) > PLATE_MAX:
        step = len(stills) / PLATE_MAX
        stills = [stills[round(i * step)] for i in range(PLATE_MAX)]
    cols = int(len(stills) ** 0.5)
    rows = (len(stills) + cols - 1) // cols
    grid = Image.new("RGB", (cols * CELL[0], rows * CELL[1]), (0, 0, 0))
    for i, s in enumerate(stills):
        cell = letterbox(Image.open(s).convert("RGB"), CELL)
        grid.paste(cell, ((i % cols) * CELL[0], (i // cols) * CELL[1]))
    dst = OUT / f"{tag}_plate.jpg"
    grid.save(dst, quality=90)
    return dst


def build_ref_video(scene, tag, nums):
    """Concat member shot refs (stream copy). Returns path or None."""
    clips = [REFS / f"shot_{n:05d}.mp4" for n in nums]
    clips = [c for c in clips if c.exists() and c.stat().st_size > 0]
    if not clips:
        return None
    dst = OUT / f"{tag}_ref.mp4"
    if len(clips) == 1:
        dst.write_bytes(clips[0].read_bytes())
        return dst
    lst = OUT / f"{tag}_concat.txt"
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", str(dst)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not dst.exists():
        print(f"    FAIL {tag}: {r.stderr[-200:]}")
        return None
    lst.unlink(missing_ok=True)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    setups = load_setups()
    if args.scene:
        want = set(args.scene.split(","))
        setups = [(s, t, n) for s, t, n in setups if s in want]

    recs = emit_ledger(setups)
    n_plate = n_vid = 0
    for (scene, tag, nums) in setups:
        plate = build_plate(scene, tag, nums)
        vid = build_ref_video(scene, tag, nums)
        if plate:
            n_plate += 1
        if vid:
            n_vid += 1
        print(f"  {tag}: {len(nums)} shots -> "
              f"{plate.name if plate else 'no-plate'}, {vid.name if vid else 'no-ref'}")

    multi = sum(1 for r in recs if r["n_members"] > 1)
    print(f"\n{len(recs)} setups ({multi} multi-shot) -> plates={n_plate}, refs={n_vid}")
    print(f"ledger: {LEDGER}")
    print(f"output: {OUT}")


if __name__ == "__main__":
    main()