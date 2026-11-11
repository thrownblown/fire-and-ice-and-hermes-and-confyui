# -*- coding: utf-8 -*-
"""Assemble the film from what is on disk.

Order is the film's order: chunks.jsonl is grouped by scene, NOT chronological, so the
list is sorted by `src_start` (the source-film timestamp each chunk covers). Sorting that
way interleaves the S and G scene namespaces into one sequence, which is the real cut.

Per chunk, the take chosen is the highest take number available in runs/yolo_output*
(t03 > t02 > t01: later takes exist because prompts were fixed afterwards). A chunk with
no take at all is filled from fullrun/output/<chunk>_full_t01.mp4 — the Sep/Oct pass that
covered all 494 chunks at 864x480. Fills are recorded in the manifest, never hidden.

The two sources differ in resolution (1344x768 new, 864x480 old) and generation, so every
segment is re-encoded to one uniform profile (1344x768 canvas, padded not stretched, h264
via NVENC on the idle 4090, aac 32 kHz stereo to match H3's own audio) and then the
segments are concatenated with stream copy. NVENC because it is ~10x faster than x264 here
and nothing else is holding the GPU.

Outputs:
  fullrun/stitched/movie_new_takes.mp4   only chunks with a real take (the current pipeline)
  fullrun/stitched/movie_full_mix.mp4    every chunk: takes + old-pass fills (plays end to end)
  fullrun/stitched/assembly_manifest.jsonl  one row per chunk: source, take, file, duration

    .venv/Scripts/python.exe runs/assemble_movie.py --limit 6 --out test   # smoke test
    .venv/Scripts/python.exe runs/assemble_movie.py                       # the real thing
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ROOT / "fullrun" / "chunks.jsonl"
OLD = ROOT / "fullrun" / "output"
STITCH = ROOT / "fullrun" / "stitched"
CANVAS = "1344:768"
VENC = ["-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "23", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", f"scale={CANVAS}:force_original_aspect_ratio=decrease,pad={CANVAS}:(ow-iw)/2:(oh-ih)/2,setsar=1"]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "32000", "-ac", "2"]


def src_secs(s: str) -> float:
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def takes_by_chunk() -> dict[str, tuple[int, Path]]:
    best: dict[str, tuple[int, Path]] = {}
    for d in sorted(ROOT.glob("runs/yolo_output*")):
        for f in d.glob("*.mp4"):
            m = re.match(r"([A-Z]\d+-c\d+)_audioOnly_t(\d+)", f.name)
            if not m:
                continue
            cid, take = m.group(1), int(m.group(2))
            if cid not in best or take > best[cid][0]:
                best[cid] = (take, f)
    return best


def ffprobe_dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def encode(src: Path, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 0 and ffprobe_dur(dst) > 0.2:
        return True                                    # resumable: never redo a segment
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
                        *VENC, *AENC, "-movflags", "+faststart", str(dst)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    ENCODE FAILED {src.name}: {(r.stderr or '').strip()[:160]}", flush=True)
        return False
    return True


def concat(segments: list[Path], out: Path, work: Path) -> float:
    lst = work / f"{out.stem}.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segments), encoding="utf-8", newline="")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", "-movflags", "+faststart", str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  concat FAILED for {out.name}: {(r.stderr or '').strip()[:200]}", flush=True)
        return 0.0
    return ffprobe_dur(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N chunks (smoke test)")
    ap.add_argument("--out", default="", help="suffix for output names, e.g. 'test'")
    ap.add_argument("--only-new", action="store_true", help="skip the old-pass fills")
    a = ap.parse_args()

    chunks = [json.loads(l) for l in CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()]
    chunks.sort(key=lambda c: src_secs(c["src_start"]))
    if a.limit:
        chunks = chunks[: a.limit]
    best = takes_by_chunk()

    segdir = STITCH / "_segments"
    segdir.mkdir(parents=True, exist_ok=True)
    rows, seg_new, seg_all, total = [], [], [], 0.0
    for i, c in enumerate(chunks, 1):
        cid = c["chunk_id"]
        take, take_path = best.get(cid, (0, None))
        if take_path is not None:
            src, kind = take_path, f"take_t{take:02d}"
        else:
            src, kind = OLD / f"{cid}_full_t01.mp4", "old_fill"
        if not src.exists():
            print(f"  {cid}: no file at all ({src.name}) — skipped", flush=True)
            continue
        if kind == "old_fill" and a.only_new:
            continue
        seg = segdir / f"{i:04d}_{cid}_{kind}.mp4"
        ok = encode(src, seg)
        if not ok:
            continue
        d = ffprobe_dur(seg)
        total += d
        rows.append({"i": i, "chunk_id": cid, "src_start": c["src_start"], "source": kind,
                     "src_file": str(src.relative_to(ROOT)).replace("\\", "/"), "seconds": round(d, 3)})
        seg_all.append(seg)
        if kind != "old_fill":
            seg_new.append(seg)
        print(f"  [{i:>3}/{len(chunks)}] {cid:<10} {kind:<10} {d:6.2f}s  {total/60:6.2f} min", flush=True)

    sfx = f"_{a.out}" if a.out else ""
    dur_all = concat(seg_all, STITCH / f"movie_full_mix{sfx}.mp4", segdir)
    dur_new = concat(seg_new, STITCH / f"movie_new_takes{sfx}.mp4", segdir) if seg_new else 0.0
    man = STITCH / f"assembly_manifest{sfx}.jsonl"
    man.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="")

    fills = sum(1 for r in rows if r["source"] == "old_fill")
    print(f"\nsegments: {len(rows)} ({len(rows)-fills} takes + {fills} old-pass fills)")
    print(f"movie_new_takes{sfx}.mp4 : {dur_new/60:.2f} min from {len(seg_new)} chunks")
    print(f"movie_full_mix{sfx}.mp4  : {dur_all/60:.2f} min from {len(seg_all)} chunks")
    print(f"manifest: {man.relative_to(ROOT)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
