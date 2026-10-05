"""Stage 1c: preprocess reference clips for H3 ref2va.

The chopped clips are BluRay-extract spec: 1920x1072 (the letterboxed master
height, not clean 16:9) at 24000/1001 fps (~23.976). H3 is a native 24fps model
and VAE-encodes the whole reference clip on every render, so:

  - fps is normalized to exactly 24 so the reference timeline lines up with the
    generated 24fps timeline (23.976 vs 24 drifts the speech/posture alignment).
  - resolution is downscaled to a clean 16:9 target so the per-render reference
    encode is cheaper (decode of 1920x1072 frames is the hidden cost).

Output lands under refs/ with a manifest; reproducible from the clips/ manifest.

Run:  .venv/Scripts/python.exe preprocess_ref.py [--res 1280:720] [--full] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLIPS = ROOT / "clips" / "full"
OUT = ROOT / "refs"
SRC_FPS = 24000 / 1001
TARGET_FPS = 24


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def ffmpeg_ref(src: Path, dst: Path, scale: str | None) -> subprocess.CompletedProcess:
    """fps-normalize (and optionally downscale) a clip into an H3 reference."""
    vf = [f"fps={TARGET_FPS}"]
    if scale:
        vf.append(f"scale={scale}")
    return run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(src),
            "-vf", ",".join(vf),
            "-c:v", "libx264", "-preset", "fast", "-crf", "16",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(dst),
        ]
    )


def probe_fps(path: Path) -> tuple[float, int, int]:
    res = run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate,width,height",
         "-of", "json", str(path)]
    )
    s = json.loads(res.stdout or "{}").get("streams", [{}])[0]
    num, _, den = (s.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or "1")
    return fps, int(s.get("width") or 0), int(s.get("height") or 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="1280:720", help="target WxH ('' to skip downscale)")
    ap.add_argument("--full", action="store_true", help="keep full res, fps-only")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shot", default=None, help="single shot id, e.g. shot_00196")
    args = ap.parse_args()

    scale = None if args.full else args.res
    OUT.mkdir(parents=True, exist_ok=True)

    clips = sorted(CLIPS.glob("shot_*.mp4"))
    if args.shot:
        clips = [CLIPS / f"{args.shot}.mp4"]
    if args.limit:
        clips = clips[: args.limit]

    manifest: list[dict] = []
    failures: list[dict] = []
    t0 = time.time()

    for i, src in enumerate(clips, 1):
        if not src.exists():
            failures.append({"shot": src.name, "stage": "missing", "stderr": "no clip"})
            continue
        dst = OUT / src.name
        fps, w, h = probe_fps(src)
        if not dst.exists():
            res = ffmpeg_ref(src, dst, scale)
            if res.returncode != 0:
                failures.append({"shot": src.name, "stage": "ref", "stderr": res.stderr[-300:]})
                print(f"  [{i}/{len(clips)}] {src.name} REF FAILED")
                continue
        nfps, nw, nh = probe_fps(dst)
        manifest.append({
            "shot": src.name, "src": f"{w}x{h}@{fps:.3f}fps",
            "ref": f"{nw}x{nh}@{nfps:.3f}fps",
        })
        print(f"  [{i}/{len(clips)}] {src.name} {w}x{h}@{fps:.3f} -> {nw}x{nh}@{nfps:.3f}")

    (OUT / "refs_manifest.json").write_text(
        json.dumps({
            "source": str(CLIPS),
            "target_fps": TARGET_FPS,
            "scale": scale,
            "count": len(manifest),
            "refs": manifest,
            "failures": failures,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n{len(manifest)} refs in {time.time() - t0:.1f}s -> {OUT}")
    print(f"manifest: {OUT / 'refs_manifest.json'}")
    if failures:
        print(f"FAILURES: {len(failures)}")
        for f in failures:
            print(f"  {f['shot']}: {f['stderr'][-200:]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
