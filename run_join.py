"""Join timecoded cues to chunks and write a per-chunk dialogue manifest."""
import json
from pathlib import Path

from core.chunker import group_shots
from core.join import join_chunks

shots = [json.loads(l) for l in open("shots.jsonl", encoding="utf-8")]
chunks = group_shots(shots, {})  # empty labels -> 3-shot cap (placeholder until VLM labels)
cues = [json.loads(l) for l in open("manifests/aligned_cues.jsonl", encoding="utf-8")]

joined = join_chunks(chunks, cues)
with_dialogue = [j for j in joined if j.cues]
print(f"{len(chunks)} chunks; {len(with_dialogue)} contain dialogue "
      f"({sum(len(j.cues) for j in joined)} cue assignments)")

print("\n--- sample chunks with dialogue ---")
for j in with_dialogue[:4]:
    print(f"  {j.chunk_id} [{j.start_s:.0f}s-{j.end_s:.0f}s]:")
    for c in j.cues:
        print(f"      {c['text'][:70]}")

Path("manifests/chunk_dialogue.jsonl").write_text(
    "\n".join(json.dumps({
        "chunk_id": j.chunk_id, "start_s": round(j.start_s, 2), "end_s": round(j.end_s, 2),
        "cues": [{"text": c["text"], "start": c["start"], "end": c["end"]} for c in j.cues],
    }) for j in joined),
    encoding="utf-8",
)
print("\nwrote manifests/chunk_dialogue.jsonl")
