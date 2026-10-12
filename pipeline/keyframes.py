"""Stage 1c: per-shot keyframe stills (first / median / last) + audio stem extraction.

Replaces the single-first-frame still with a three-sample set per shot, and
adds two audio artifacts:

  1. a per-shot audio stem (the shot's own interval, from the master)
  2. the full continuous master audio track, decoded once to WAV

Blank/near-blank samples are flagged by file size so the VLM pass can skip
them instead of being handed black frames.

Run:  .venv/Scripts/python.exe keyframes.py --minutes 30 --offset 30
      .venv/Scripts/python.exe keyframes.py --minutes 10 --no-audio-full
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / "Fire.And.Ice.1983.1080p.BluRay.x264-[YTS.AM].mp4"
SHOTS = ROOT / "shots.jsonl"
TB_DEN = 24000

# A JPEG smaller than this at 1920x1072 is effectively a blank / near-black
# frame. Calibrated from the opening-title shots (13-15 KB observed).
BLANK_STILL_BYTES = 20000


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def grab_still(src: Path, dst: Path, frame_index: int) -> subprocess.CompletedProcess:
    """Extract one frame by index from an already-sliced clip.

    select=eq(n\\,N) is exact: it counts decoded frames from the clip start,
    so index 0 is the shot's true first frame and n-1 is its last.
    """
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
            "-vf", f"select=eq(n\\,{frame_index})",
            "-frames:v", "1", "-q:v", "2",
            str(dst),
        ]
    )


def extract_stem(src: Path, dst: Path, start_s: float, dur_s: float) -> subprocess.CompletedProcess:
    """Per-shot audio stem, decoded to WAV at the master's native 48 kHz."""
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start_s:.9f}",
            "-i", str(src),
            "-t", f"{dur_s:.9f}",
            "-vn", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
            str(dst),
        ]
    )


def extract_full_audio(src: Path, dst: Path) -> subprocess.CompletedProcess:
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
            "-vn", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
            str(dst),
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=10.0, help="length of window")
    ap.add_argument("--offset", type=float, default=0.0, help="window start in minutes")
    ap.add_argument("--audio-full", dest="audio_full", action="store_true", default=True)
    ap.add_argument("--no-audio-full", dest="audio_full", action="store_false")
    ap.add_argument("--tag", default=None, help="override output window tag")
    args = ap.parse_args()

    start_pts_cut = int(args.offset * 60 * TB_DEN)
    end_pts_cut = int((args.offset + args.minutes) * 60 * TB_DEN)

    all_shots = [json.loads(l) for l in SHOTS.open(encoding="utf-8")]
    selected = [s for s in all_shots if start_pts_cut <= s["start_pts"] < end_pts_cut]

    if not selected:
        print("no shots in window")
        return 1

    tag = args.tag or f"m{int(args.offset):03d}_{int(args.offset + args.minutes):03d}"
    # Clips live in clips/<tag>/ when tagged, and in clips/ for the
    # original untagged first-10-minutes window. Try both so the two
    # scripts stay compatible either way.
    if args.tag:
        clips_dir = ROOT / "clips" / args.tag
    else:
        tagged = ROOT / "clips" / tag
        clips_dir = tagged if tagged.exists() else ROOT / "clips"
    stills_dir = ROOT / "stills" / tag
    audio_dir = ROOT / "audio"
    stems_dir = audio_dir / "stems" / tag
    for d in (stills_dir, stems_dir):
        d.mkdir(parents=True, exist_ok=True)

    lo = selected[0]["start_tc"]
    hi = selected[-1]["end_tc"]
    print(f"window {args.offset:.1f}-{args.offset + args.minutes:.1f} min  tag={tag}")
    print(f"{len(selected)} shots  {lo} -> {hi}")
    print(f"coverage {sum(s['duration_seconds'] for s in selected):.1f}s")

    # Full master audio: decode once, only if absent.
    audio_manifest: dict = {}
    if args.audio_full:
        full_wav = audio_dir / "master_audio_48k_stereo.wav"
        if not full_wav.exists():
            print("\ndecoding full master audio (81 min, this takes a moment)")
            t0 = time.time()
            res = extract_full_audio(MASTER, full_wav)
            if res.returncode != 0:
                print(f"FULL AUDIO FAILED: {res.stderr[-300:]}")
                return 2
            print(f"  done in {time.time() - t0:.1f}s  {full_wav.stat().st_size / 1e6:.1f} MB")
        else:
            print(f"\nfull master audio present: {full_wav.name} "
                  f"({full_wav.stat().st_size / 1e6:.1f} MB)")
        audio_manifest["full_track"] = {
            "file": str(full_wav.relative_to(ROOT)),
            "sample_rate": 48000,
            "channels": 2,
            "codec": "pcm_s16le",
            "size_bytes": full_wav.stat().st_size,
            "source": MASTER.name,
        }

    manifest = []
    failures = []
    blanks = []
    t0 = time.time()

    for i, shot in enumerate(selected, 1):
        sid = shot["shot_id"].replace("shot:", "shot_")
        clip = clips_dir / f"{sid}.mp4"
        if not clip.exists():
            failures.append({"shot_id": shot["shot_id"], "stage": "missing_clip"})
            print(f"  [{i}/{len(selected)}] {sid} NO CLIP - run chop.py first")
            continue

        n = shot["frame_count"]
        # First, median, last. For n<3 the indices collapse; dedupe while
        # keeping order so a 1-frame shot still yields one still.
        picks = sorted({0, n // 2, n - 1})

        samples = []
        for idx in picks:
            dst = stills_dir / f"{sid}_f{idx:05d}.jpg"
            if not dst.exists():
                res = grab_still(clip, dst, idx)
                if res.returncode != 0:
                    failures.append({"shot_id": shot["shot_id"], "stage": "still",
                                     "frame": idx, "stderr": res.stderr[-300:]})
                    continue
            size = dst.stat().st_size
            is_blank = size < BLANK_STILL_BYTES
            if is_blank:
                blanks.append(f"{sid}_f{idx:05d}")
            samples.append({
                "frame_index": idx,
                "file": str(dst.relative_to(ROOT)),
                "size_bytes": size,
                "blank": is_blank,
                "role": {0: "first"}.get(idx, "last" if idx == n - 1 else "median"),
            })

        # Per-shot audio stem
        stem = stems_dir / f"{sid}.wav"
        if not stem.exists():
            res = extract_stem(MASTER, stem, shot["start_pts"] / TB_DEN,
                               shot["duration_seconds"])
            if res.returncode != 0:
                failures.append({"shot_id": shot["shot_id"], "stage": "stem",
                                 "stderr": res.stderr[-300:]})

        manifest.append({
            "shot_id": shot["shot_id"],
            "start_tc": shot["start_tc"],
            "end_tc": shot["end_tc"],
            "duration_seconds": shot["duration_seconds"],
            "frame_count": n,
            "still_samples": samples,
            "stem": str(stem.relative_to(ROOT)) if stem.exists() else None,
        })

        roles = ",".join(f"{s['role']}:{s['frame_index']}" for s in samples)
        flag = " [blank!]" if any(s["blank"] for s in samples) else ""
        print(f"  [{i}/{len(selected)}] {sid} n={n:5d} stills=[{roles}]{flag}")

    out = ROOT / "stills" / f"keyframes_manifest_{tag}.json"
    out.write_text(
        json.dumps({
            "window": {"offset_minutes": args.offset, "minutes": args.minutes,
                       "tag": tag, "first_tc": lo, "last_tc": hi},
            "sampling": {"policy": "first_median_last",
                         "blank_still_threshold_bytes": BLANK_STILL_BYTES},
            "audio": audio_manifest,
            "shot_count": len(manifest),
            "total_stills": sum(len(m["still_samples"]) for m in manifest),
            "blank_stills": len(blanks),
            "shots": manifest,
            "failures": failures,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n{len(manifest)} shots processed in {time.time() - t0:.1f}s")
    print(f"stills -> {stills_dir}")
    print(f"stems  -> {stems_dir}")
    print(f"manifest: {out.name}")
    print(f"total stills: {sum(len(m['still_samples']) for m in manifest)}  "
          f"blank-flagged: {len(blanks)}")
    if blanks:
        print(f"blank stills (VLM should skip): {', '.join(blanks[:12])}"
              + (" ..." if len(blanks) > 12 else ""))
    if failures:
        print(f"FAILURES: {len(failures)}")
        for f in failures[:8]:
            print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
