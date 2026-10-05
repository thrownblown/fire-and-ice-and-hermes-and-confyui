"""Transcribe the full master audio and save timed segments as JSONL."""
import json
from pathlib import Path

from core.asr import transcribe

wav = Path("audio/master_audio_48k_stereo.wav")
out = Path("audio/asr_segments.jsonl")

recs = transcribe(wav)
with open(out, "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r) + "\n")

print(f"wrote {len(recs)} segments -> {out}")
