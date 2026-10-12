"""Build voice-data.js for the character page's voice-clip picker.

Parses audio/voice-review.md (the curated list of 223 clean Demucs vocal lines
across 12 speakers, with duration and text) and emits a baked
browser/voice-data.js so the shot browser can render playable <audio> clips on
the character page without fetch() (file:// safe).

Each line's audio path is derived from its id + speaker:
  audio/lines/L237_NEKRON.wav

Output (written to E:/FNI):
  browser/voice-data.js -> window.VOICEDATA = { "NEKRON": [{id,dur,text,src}, ...], ... }

Run:  .venv/Scripts/python.exe tools/build_voice_data.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"E:/FNI")
MD = ROOT / "audio" / "voice-review.md"
LINES = ROOT / "audio" / "lines"
OUT = ROOT / "browser" / "voice-data.js"

SECTION = re.compile(r"^##\s+(.+?)\s*—")               # "## NEKRON — 33 clean lines, 95s"
ROW = re.compile(r"^\|\s*\[ \]\s*\|\s*(L\d+)\s*\|\s*([\d.]+)s\s*\|\s*(.*?)\s*\|\s*$")


def main() -> int:
    data: dict[str, list[dict]] = {}
    cur: str | None = None
    for raw in MD.read_text(encoding="utf-8").splitlines():
        m = SECTION.match(raw)
        if m:
            cur = m.group(1).strip()
            data.setdefault(cur, [])
            continue
        m = ROW.match(raw)
        if m and cur:
            data[cur].append({"id": m.group(1), "dur": m.group(2), "text": m.group(3).strip()})

    # attach audio src and verify the clip exists (catch speaker-name mismatches)
    missing = []
    total = 0
    for speaker, lines in data.items():
        for ln in lines:
            src = f"audio/lines/{ln['id']}_{speaker}.wav"
            ln["src"] = src
            total += 1
            if not (LINES / f"{ln['id']}_{speaker}.wav").exists():
                missing.append(src)

    js = "window.VOICEDATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"
    OUT.write_text(js, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    print(f"speakers: {len(data)}   lines: {total}")
    if missing:
        print(f"MISSING CLIPS ({len(missing)}):")
        for m in missing:
            print(f"  {m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
