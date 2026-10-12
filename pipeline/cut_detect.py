"""Stage 1: source-master hash + cut detection -> shots.jsonl

Fire & Ice v0.3 pipeline. Reads the source master, hashes it, runs
PySceneDetect, and emits one record per shot with:
  - PTS in/out at the source timebase (1/24000)
  - frame in/out at 24000/1001 fps
  - exact rational duration
  - H3 frame-grid mapping (17k+5 alignment, 124-frame qualified minimum)
  - an H3 duration request guess (whole seconds, 4-15s) plus the
    aligned frame count that a naive `ceil(24*T)` request would yield

Run:  .venv/Scripts/python.exe cut_detect.py
Outputs: shots.jsonl, master.json, cut_detect.log
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

from scenedetect import ContentDetector, SceneManager, open_video

ROOT = Path(__file__).resolve().parent
MASTER = ROOT / "Fire.And.Ice.1983.1080p.BluRay.x264-[YTS.AM].mp4"

# Source master properties, measured with ffprobe (see master.json).
VIDEO_TIME_BASE = Fraction(1, 24000)
FPS = Fraction(24000, 1001)
AUDIO_SAMPLE_RATE = 48000

# H3 frame-grid contract (H3_Render_Strategy_v0_3 §6).
H3_GRID_BASE = 5
H3_GRID_STRIDE = 17
H3_MIN_QUALIFIED_FRAMES = 124
H3_TRAINED_MAX_FRAMES = 362
H3_NOMINAL_FPS = 24

# Cut detection tuning. ContentDetector expects a frame-delta score;
# 27 is scenedetect's default and a reasonable starting point for a
# 1983 BluRay transfer. min_scene_len guards against held-cel chatter.
CONTENT_THRESHOLD = 27.0
MIN_SCENE_LEN_FRAMES = 12  # ~0.5s at 23.976


def sha256_file(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def frame_to_pts(frame: int) -> int:
    """Frame index at 24000/1001 fps -> source PTS at timebase 1/24000.

    Frame duration is 1001/24000 s, so one frame advances PTS by exactly
    1001 ticks. Integer-exact: PTS == frame * 1001.
    """
    return frame * FPS.denominator  # FPS.denominator == 1001


def seconds_to_frames(seconds: float) -> int:
    """Round-half-up absolute conversion, per fi_core time_map rounding policy."""
    exact = Fraction(seconds) * FPS
    return (exact.numerator * 2 // exact.denominator + 1) // 2


def h3_align(requested_frames: int) -> int:
    """5 + 17 * ceil((n - 5) / 17), floored at the qualified minimum."""
    if requested_frames <= H3_GRID_BASE:
        return H3_MIN_QUALIFIED_FRAMES
    extra = -(-(requested_frames - H3_GRID_BASE) // H3_GRID_STRIDE)  # ceil div
    return max(H3_MIN_QUALIFIED_FRAMES, H3_GRID_BASE + H3_GRID_STRIDE * extra)


def detect() -> dict:
    log = []

    def emit(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log.append(line)

    emit(f"hashing master {MASTER.name}")
    t0 = time.time()
    digest = sha256_file(MASTER)
    emit(f"sha256={digest} in {time.time() - t0:.1f}s")

    emit("opening video for cut detection")
    video = open_video(str(MASTER))
    fps = float(video.frame_rate)
    emit(f"reported fps={fps:.6f} duration={video.duration}")
    assert abs(fps - float(FPS)) < 1e-6, f"unexpected fps {fps}"

    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(
            threshold=CONTENT_THRESHOLD,
            min_scene_len=MIN_SCENE_LEN_FRAMES,
        )
    )

    emit(f"detecting cuts (threshold={CONTENT_THRESHOLD}, min_len={MIN_SCENE_LEN_FRAMES})")
    t0 = time.time()
    scene_manager.detect_scenes(video, show_progress=False)
    elapsed = time.time() - t0
    emit(f"detection finished in {elapsed:.1f}s")

    scenes = scene_manager.get_scene_list(start_in_scene=True)
    emit(f"detected {len(scenes)} scenes")

    shots = []
    for idx, (start, end) in enumerate(scenes):
        start_f = start.get_frames()
        end_f = end.get_frames()  # exclusive: first frame of next shot
        dur_f = end_f - start_f
        dur_s = float(Fraction(dur_f, 1) / FPS)

        # What a naive request would look like, and what H3 would actually emit.
        requested = max(1, round(dur_s * H3_NOMINAL_FPS))
        aligned = h3_align(requested)

        shots.append(
            {
                "shot_id": f"shot:{idx + 1:05d}",
                "index": idx + 1,
                "start_pts": frame_to_pts(start_f),
                "end_pts": frame_to_pts(end_f),
                "start_frame": start_f,
                "end_frame": end_f,
                "frame_count": dur_f,
                "duration_seconds": round(dur_s, 6),
                "duration_rational": {"num": dur_f * 1001, "den": 24000},
                "start_tc": start.get_timecode(),
                "end_tc": end.get_timecode(),
                "h3": {
                    "requested_generated_frames": requested,
                    "aligned_generated_frames": aligned,
                    "aligned_is_minimum_floored": aligned == H3_MIN_QUALIFIED_FRAMES,
                    "exceeds_trained_max": aligned > H3_TRAINED_MAX_FRAMES,
                    "generated_seconds": round(aligned / H3_NOMINAL_FPS, 4),
                },
            }
        )

    covered_frames = sum(s["frame_count"] for s in shots)
    covered_secs = float(Fraction(covered_frames, 1) / FPS)
    emit(f"coverage: {covered_frames} frames / {covered_secs:.3f}s")

    master = {
        "id": "master:fire_and_ice_1983_yts",
        "revision": 1,
        "artifact": {
            "path": MASTER.name,
            "sha256": f"sha256:{digest}",
            "size_bytes": MASTER.stat().st_size,
            "codec": "h264",
            "width": 1920,
            "height": 1072,
            "pix_fmt": "yuv420p",
        },
        "video_time_base": {"num": 1, "den": 24000},
        "fps": {"num": 24000, "den": 1001},
        "nb_frames": 117436,
        "duration_seconds": 4898.059833,
        "audio": {
            "codec": "aac",
            "sample_rate": 48000,
            "channels": 2,
            "channel_layout": "stereo",
            "time_base": {"num": 1, "den": 48000},
            "duration_seconds": 4898.069,
        },
        "cut_detection": {
            "detector": "ContentDetector",
            "threshold": CONTENT_THRESHOLD,
            "min_scene_len_frames": MIN_SCENE_LEN_FRAMES,
            "start_in_scene": True,
            "scenedetect_version": "0.7.1",
            "scene_count": len(shots),
        },
    }

    return {"master": master, "shots": shots, "log": log}


def main() -> int:
    result = detect()

    master_path = ROOT / "master.json"
    shots_path = ROOT / "shots.jsonl"
    log_path = ROOT / "cut_detect.log"

    master_path.write_text(json.dumps(result["master"], indent=2) + "\n", encoding="utf-8")
    with shots_path.open("w", encoding="utf-8") as fh:
        for shot in result["shots"]:
            fh.write(json.dumps(shot) + "\n")
    log_path.write_text("\n".join(result["log"]) + "\n", encoding="utf-8")

    shots = result["shots"]
    print(f"\nwrote {master_path.name}, {shots_path.name} ({len(shots)} shots), {log_path.name}")

    if shots:
        durations = sorted(s["duration_seconds"] for s in shots)
        n = len(durations)
        print(f"\nduration: min={durations[0]:.3f}s  median={durations[n // 2]:.3f}s  max={durations[-1]:.3f}s")

        over = sum(1 for s in shots if s["h3"]["exceeds_trained_max"])
        floored = sum(1 for s in shots if s["h3"]["aligned_is_minimum_floored"])
        print(f"shots exceeding H3 trained max (362f): {over}")
        print(f"shots floored to 124f minimum:         {floored}")
        print(f"\ntotal H3 generated seconds if 1 take/shot: {sum(s['h3']['generated_seconds'] for s in shots):.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
