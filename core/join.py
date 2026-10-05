"""Assign timecoded cues to chunks by time overlap."""
from __future__ import annotations

from dataclasses import dataclass

TB_DEN = 24000


@dataclass
class ChunkDialogue:
    chunk_id: str
    start_s: float
    end_s: float
    cues: list[dict]


def pts_to_seconds(pts: int) -> float:
    return pts / TB_DEN


def join_chunks(chunks, cues) -> list[ChunkDialogue]:
    """chunks: objects with .id/.start_pts/.end_pts.
    cues: dicts with start/end in seconds; start=None means unmatched (skipped).
    A cue overlaps the chunk if cue.start < chunk.end_s and cue.end > chunk.start_s.
    """
    results: list[ChunkDialogue] = []
    for c in chunks:
        cs = pts_to_seconds(c.start_pts)
        ce = pts_to_seconds(c.end_pts)
        inside = [
            cu for cu in cues
            if cu.get("start") is not None
            and cu["start"] < ce and cu["end"] > cs
        ]
        results.append(ChunkDialogue(chunk_id=c.id, start_s=cs, end_s=ce, cues=inside))
    return results
