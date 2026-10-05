"""Monotonic fuzzy alignment of ASR segments to script cues.

Both sequences are in narrative order, so alignment is monotonic: each script
cue maps to at most one ASR segment (in order). Text may differ (ASR errors,
transcript wording), so the match score is a blended token/character similarity.
Unmatched cues (below min_score) get start/end = None.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

LOOKAHEAD = 8  # max segments to search ahead for a cue's match


@dataclass
class AlignedCue:
    cue_index: int
    cue_text: str
    page: int
    start: float | None
    end: float | None
    score: float


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def similarity(a: str, b: str) -> float:
    """Blend of token Jaccard and character ratio, 0.0..1.0. Pure."""
    a = _norm(a)
    b = _norm(b)
    if not a or not b:
        return 0.0
    ta, tb = set(a.split()), set(b.split())
    union = ta | tb
    jac = len(ta & tb) / len(union) if union else 0.0
    char = SequenceMatcher(None, a, b).ratio()
    return 0.5 * jac + 0.5 * char


def align(cues, segments, min_score: float = 0.35) -> list[AlignedCue]:
    """cues: ordered objects with .index/.page/.text.
    segments: ordered list of dicts with start/end/text (floats).
    Returns one AlignedCue per cue, monotonic in time."""
    results: list[AlignedCue] = []
    seg_idx = 0
    for cue in cues:
        best_j = -1
        best_score = 0.0
        hi = min(len(segments), seg_idx + LOOKAHEAD)
        for j in range(seg_idx, hi):
            s = similarity(cue.text, segments[j]["text"])
            if s > best_score:
                best_score = s
                best_j = j
        if best_j >= 0 and best_score >= min_score:
            seg = segments[best_j]
            results.append(AlignedCue(
                cue_index=cue.index, cue_text=cue.text, page=cue.page,
                start=seg["start"], end=seg["end"], score=round(best_score, 3),
            ))
            seg_idx = best_j + 1
        else:
            results.append(AlignedCue(
                cue_index=cue.index, cue_text=cue.text, page=cue.page,
                start=None, end=None, score=0.0,
            ))
    return results
