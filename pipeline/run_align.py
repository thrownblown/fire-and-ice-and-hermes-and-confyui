"""Align full-film ASR segments to script cues and write a timecoded manifest."""
import json
from pathlib import Path

from core.align import align
from core.script import extract_pdf_text, merge_sentences, parse_script

cues = merge_sentences(parse_script(extract_pdf_text(Path("docs/doc.pdf"))))
segs = [json.loads(l) for l in open("audio/asr_segments.jsonl", encoding="utf-8")]

out = align(cues, segs)
matched = [c for c in out if c.start is not None]
rate = 100 * len(matched) / len(cues) if cues else 0
print(f"{len(cues)} cues, {len(segs)} ASR segments, "
      f"{len(matched)} matched ({rate:.1f}%)")

print("\n--- first 10 matches ---")
for c in out[:10]:
    t = f"{c.start:>8.2f}" if c.start is not None else "     NONE"
    print(f"  [{t}] ({c.score:.2f}) {c.cue_text[:60]}")

print("\n--- first 5 unmatched ---")
for c in [c for c in out if c.start is None][:5]:
    print(f"  {c.cue_text[:60]}")

Path("manifests/aligned_cues.jsonl").write_text(
    "\n".join(json.dumps({
        "cue_index": c.cue_index, "page": c.page, "text": c.cue_text,
        "start": c.start, "end": c.end, "score": c.score,
    }) for c in out),
    encoding="utf-8",
)
print("\nwrote manifests/aligned_cues.jsonl")
