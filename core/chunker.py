"""Group adjacent shots into 2-3 shot chunks by visual continuity.

A chunk continues while the next shot shares the same location AND the
same character set (within overlap tolerance). Hard cap: 3 shots per chunk.
A shot flanked by discontinuities on both on both sides becomes a 1-shot chunk.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_SHOTS_PER_CHUNK = 3


@dataclass
class Chunk:
    id: str
    shot_ids: list[str]
    start_pts: int
    end_pts: int
    location: str
    characters: list[str]


def _empty_label() -> dict:
    return {"location": "", "characters": []}


def _same_space(a: dict, b: dict) -> bool:
    """Visual continuity: same location and overlapping character sets.
    An empty character set on either side is treated as compatible."""
    if a["location"] != b["location"]:
        return False
    if a["characters"] and b["characters"]:
        return bool(set(a["characters"]) & set(b["characters"]))
    return True


def group_shots(shots: list[dict], labels: dict) -> list[Chunk]:
    """shots: ordered list of shot records (shot_id, start_pts, end_pts).
    labels: {shot_id: {"location": str, "characters": list[str]}}."""
    groups: list[list[dict]] = []
    current: list[dict] = []
    for shot in shots:
        lab = labels.get(shot["shot_id"], _empty_label())
        if current:
            prev = labels.get(current[-1]["shot_id"], _empty_label())
            if not _same_space(prev, lab) or len(current) >= MAX_SHOTS_PER_CHUNK:
                groups.append(current)
                current = []
        current.append(shot)
    if current:
        groups.append(current)

    chunks: list[Chunk] = []
    for i, g in enumerate(groups, 1):
        first, last = g[0], g[-1]
        lab = labels.get(first["shot_id"], _empty_label())
        chunks.append(Chunk(
            id=f"chunk_{i:05d}",
            shot_ids=[s["shot_id"] for s in g],
            start_pts=first["start_pts"],
            end_pts=last["end_pts"],
            location=lab["location"],
            characters=lab["characters"],
        ))
    return chunks
