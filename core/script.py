"""Extract ordered cue candidates from the Fire & Ice script PDF.

The PDF is a Scripts.com transcript: 10 pages of running dialogue with
"*Page N/10*" markers and occasional "-" prefixed speaker turns. This
module pulls text and splits it into ordered cue candidates; it does NOT
attribute speakers or split sentences — that is the VLM/ASR stage's job.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_PAGE_MARKER = re.compile(r"Page\s+(\d+)\s*/\s*\d+")
_SKIP = {"Scripts.com", "Fire And Ice", "By Roy Thomas"}


@dataclass
class Cue:
    index: int
    page: int
    text: str


def parse_script(text: str) -> list[Cue]:
    """Split raw script text into ordered cue candidates.

    Each non-empty, non-header line becomes one cue. The page number is
    taken from the nearest preceding "Page N/M" marker. Dialogue text is
    preserved verbatim — no normalization, no speaker guessing.
    """
    cues: list[Cue] = []
    page = 1
    for raw in text.splitlines():
        line = raw.strip()
        m = _PAGE_MARKER.search(line)
        if m:
            page = int(m.group(1))
            continue
        if not line or line in _SKIP or line.isdigit():
            continue
        cues.append(Cue(index=len(cues), page=page, text=line))
    return cues


def merge_sentences(cues: list[Cue]) -> list[Cue]:
    """Merge line-wrapped fragments into sentence-level cues.

    The PDF's lines are arbitrary text wrapping, not semantic lines: a single
    spoken sentence is often split across several fragments ("...her realm..."
    / "to all the regions..."). A sentence ends at '.', '!', or '?' (but not
    the trailing-ellipsis continuation "..."). A leading '-' speaker-turn
    marker is stripped.
    """
    merged: list[Cue] = []
    buf: list[str] = []
    page = 1
    for cue in cues:
        t = cue.text.strip()
        if not t:
            continue
        if t.startswith("-"):
            t = t[1:].strip()
        if not buf:
            page = cue.page
        buf.append(t)
        if t.endswith((".", "!", "?")) and not t.endswith("..."):
            merged.append(Cue(index=len(merged), page=page, text=" ".join(buf)))
            buf = []
    if buf:
        merged.append(Cue(index=len(merged), page=page, text=" ".join(buf)))
    return merged


def extract_pdf_text(pdf_path: Path) -> str:
    """Return concatenated text of all pages of the PDF."""
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
