"""Extract per-chunk audio spans from the continuous master WAV.

Audio is always cut from the continuous track, never concatenated from
per-shot stems (concatenation accumulates sample-boundary drift).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

TB_DEN = 24000  # source timebase


def pts_to_seconds(pts: int) -> float:
    return pts / TB_DEN


def build_command(master_wav: Path, start_pts: int, end_pts: int, out: Path) -> list[str]:
    start_s = pts_to_seconds(start_pts)
    dur_s = pts_to_seconds(end_pts - start_pts)
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{start_s:.9f}",
        "-i", str(master_wav),
        "-t", f"{dur_s:.9f}",
        "-vn", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
        str(out),
    ]


def extract_chunk_audio(master_wav: Path, start_pts: int, end_pts: int, out: Path) -> None:
    res = subprocess.run(
        build_command(master_wav, start_pts, end_pts, out),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if res.returncode != 0:
        raise RuntimeError(f"chunk audio extraction failed: {res.stderr[-400:]}")
