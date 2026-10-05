"""Stage 1b: extract the first N minutes of shots as individual clip files.

Slices the source master on the cut boundaries from shots.jsonl, writing
one lossless-ish clip per shot plus a re-encoded proxy and a start-frame
still for each. Everything lands under clips/ with a manifest so the
extraction is reproducible from shots.jsonl alone.

Run:  .venv/Scripts/python.exe chop.py [--minutes 10] [--limit N]
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
OUT = ROOT / "clips"
PROXY = OUT / "proxy"
STILLS = OUT / "stills"

FPS = 24000 / 1001
TB_DEN = 24000  # source timebase 1/24000


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def ffmpeg_exact(src: Path, dst: Path, start_pts: int, end_pts: int, frames: int) -> subprocess.CompletedProcess:
    """Frame-exact slice via re-encode.

    The master is a long-GOP BluRay encode (~10.4s between keyframes).
    Stream copy cannot extract a 2.4s shot that contains no keyframe, so
    slices are re-encoded. -ss before -i is decode-accurate when the
    output is re-encoded (no keyframe snapping), and -frames:v pins the
    exact frame count. The master itself is never modified; these are
    derivatives with a recorded transform.
    """
    start_s = start_pts / TB_DEN
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start_s:.9f}",
            "-i", str(src),
            "-frames:v", str(frames),
            "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "fast", "-crf", "14",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(dst),
        ]
    )


def ffmpeg_proxy(src: Path, dst: Path) -> subprocess.CompletedProcess:
    """Downscaled proxy for fast review."""
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
            "-vf", "scale=640:-2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
            "-c:a", "aac", "-b:a", "96k",
            str(dst),
        ]
    )


def ffmpeg_still(src: Path, dst: Path) -> subprocess.CompletedProcess:
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src), "-frames:v", "1", "-q:v", "2",
            str(dst),
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=10.0, help="length of window")
    ap.add_argument("--offset", type=float, default=0.0, help="window start in minutes")
    ap.add_argument("--limit", type=int, default=0, help="cap number of shots (0 = all)")
    ap.add_argument("--tag", default=None, help="override output window tag")
    ap.add_argument("--no-proxy", action="store_true")
    args = ap.parse_args()

    if args.tag:
        global OUT, PROXY, STILLS
        OUT = ROOT / "clips" / args.tag
        PROXY = OUT / "proxy"
        STILLS = OUT / "stills"

    for d in (OUT, PROXY, STILLS):
        d.mkdir(parents=True, exist_ok=True)

    all_shots = [json.loads(l) for l in SHOTS.open(encoding="utf-8")]
    lo_pts = int(args.offset * 60 * TB_DEN)
    hi_pts = int((args.offset + args.minutes) * 60 * TB_DEN)
    selected = [s for s in all_shots if lo_pts <= s["start_pts"] < hi_pts]
    if args.limit:
        selected = selected[: args.limit]

    # Fail loudly on degenerate PTS rather than writing zero-length clips.
    if any(s["end_pts"] <= s["start_pts"] for s in selected):
        bad = [s["shot_id"] for s in selected if s["end_pts"] <= s["start_pts"]][:5]
        print(f"FATAL: {len(bad)}+ shots have end_pts <= start_pts (e.g. {bad})")
        print("shots.jsonl is not usable; re-run cut_detect.py first.")
        return 2

    # Sanity-check the PTS<->frame relationship on a sample.
    for s in selected[:3]:
        expect = s["start_frame"] * 1001
        if s["start_pts"] != expect:
            print(f"FATAL: {s['shot_id']} start_pts={s['start_pts']} != frame*1001={expect}")
            return 2

    print(f"master: {MASTER.name}")
    print(f"selecting {len(selected)} shots starting before {args.minutes:.1f} min")
    print(f"coverage: {sum(s['duration_seconds'] for s in selected):.1f}s "
          f"through {selected[-1]['end_tc']}")
    by_id = {s["shot_id"]: s for s in all_shots}
    manifest: list[dict] = []
    failures: list[dict] = []
    t_start = time.time()

    for i, shot in enumerate(selected, 1):
        sid = shot["shot_id"].replace("shot:", "shot_")
        clip = OUT / f"{sid}.mp4"
        entry = {**shot, "clip": clip.name}

        if not clip.exists():
            res = ffmpeg_exact(MASTER, clip, shot["start_pts"], shot["end_pts"], shot["frame_count"])
            if res.returncode != 0:
                failures.append({"shot_id": shot["shot_id"], "stage": "slice", "stderr": res.stderr[-400:]})
                print(f"  [{i}/{len(selected)}] {sid} SLICE FAILED")
                continue

        # verify actual frames/audio of the written clip
        probe = run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-count_frames", "-show_entries", "stream=nb_read_frames,r_frame_rate",
             "-of", "json", str(clip)]
        )
        clip_frames = None
        if probe.returncode == 0:
            streams = json.loads(probe.stdout or "{}").get("streams", [])
            if streams:
                raw = streams[0].get("nb_read_frames")
                clip_frames = int(raw) if raw else None
        entry["extracted_frame_count"] = clip_frames
        entry["frame_count_delta"] = (
            None if clip_frames is None else clip_frames - shot["frame_count"]
        )

        if not args.no_proxy:
            p = PROXY / f"{sid}.mp4"
            if not p.exists():
                ffmpeg_proxy(clip, p)

        still = STILLS / f"{sid}.jpg"
        if not still.exists():
            ffmpeg_still(clip, still)

        manifest.append(entry)
        print(f"  [{i}/{len(selected)}] {sid} {shot['start_tc']} "
              f"dur={shot['duration_seconds']:.3f}s frames={shot['frame_count']} "
              f"-> extracted={clip_frames}")

    (OUT / "clips_manifest.json").write_text(
        json.dumps(
            {
                "source_manifest": "shots.jsonl",
                "master": MASTER.name,
                "cutoff_minutes": args.minutes,
                "shot_count": len(manifest),
                "duration_seconds": round(sum(s["duration_seconds"] for s in manifest), 3),
                "total_frames": sum(s["frame_count"] for s in manifest),
                "clips": manifest,
                "failures": failures,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"\n{len(manifest)} clips in {time.time() - t_start:.1f}s -> {OUT}")
    print(f"manifest: {OUT / 'clips_manifest.json'}")
    if failures:
        print(f"FAILURES: {len(failures)}")
        for f in failures:
            print(f"  {f['shot_id']}: {f['stderr'][-200:]}")

    deltas = [c["frame_count_delta"] for c in manifest if c["frame_count_delta"] is not None]
    if deltas:
        nonzero = [d for d in deltas if d != 0]
        print(f"\nframe-count fidelity: {len(deltas) - len(nonzero)}/{len(deltas)} exact, "
              f"{len(nonzero)} off by {sorted(set(nonzero))[:6]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
