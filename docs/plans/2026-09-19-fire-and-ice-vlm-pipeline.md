# Fire & Ice — VLM Pipeline (Stage 2) Implementation Plan

> **For implementer:** Use TDD throughout. Write failing test first. Watch it fail. Then implement.

**Goal:** Build the Stage 2 correlation + chunking pipeline: parse the script PDF into cues, transcribe the master audio with ASR, label shots with a local VLM, group shots into 2–3-shot chunks by visual continuity, and extract per-chunk audio stems.

**Architecture:** Five small Python modules under `core/`, each with a pure, unit-testable core and a thin I/O shell. Deterministic components (script, chunker, chunk_audio) are full TDD; the VLM and ASR wrappers TDD their pure parts and qualify their I/O on the first 10-minute window.

**Tech Stack:** Python 3.11 (venv at `.venv`), pytest, pypdf, faster-whisper (local GPU), pydantic, requests (LM Studio OpenAI-compatible HTTP), ffmpeg.

**Note:** `E:\FNI` is not a git repo. The commit step is skipped for every task unless you initialize one — do not `git init` without asking.

---

## Task 0: Scaffold + dependencies

**Files:**
- Create: `core/__init__.py` (empty)

**Step 1: Install dependencies**

```bash
cd /e/FNI && uv pip install --python .venv/Scripts/python.exe pytest pypdf pydantic requests faster-whisper
```

**Expected:** all packages install. Note: faster-whisper pulls ctranslate2/onnxruntime; first ASR run downloads the whisper model (~3 GB, cached locally).

**Step 2: Verify pytest runs**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest --version
```

**Expected:** pytest version printed, no error.

---

## Task 1: Script parser (`core/script.py`)

**Files:**
- Create: `core/script.py`
- Test: `tests/test_script.py`

**Step 1: Write the failing test** — `tests/test_script.py`

```python
from core.script import parse_script

SAMPLE = (
    "Scripts.com\n"
    "Fire And Ice\n"
    "By Roy Thomas\n"
    "*Page 1/10*\n"
    "And her ambition was to extend her realm...\n"
    "*Page 2/10*\n"
    "- Perhaps. You will present our demands...\n"
)


def test_empty_text_returns_no_cues():
    assert parse_script("") == []


def test_headers_are_skipped():
    texts = [c.text for c in parse_script(SAMPLE)]
    for h in ("Scripts.com", "Fire And Ice", "By Roy Thomas"):
        assert h not in texts


def test_page_numbers_are_tracked():
    cues = parse_script(SAMPLE)
    assert cues[0].page == 1
    assert cues[1].page == 2


def test_text_preserved_verbatim():
    cues = parse_script("And her ambition was to extend her realm... to all the regions")
    assert cues[0].text == "And her ambition was to extend her realm... to all the regions"
```

**Step 2: Run test — confirm it fails**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_script.py -v
```

**Expected:** FAIL — `ModuleNotFoundError: No module named 'core'`

**Step 3: Write minimal implementation** — `core/script.py`

```python
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
        if _PAGE_MARKER.search(line):
            page = int(_PAGE_MARKER.search(line).group(1))
            continue
        if not line or line in _SKIP:
            continue
        cues.append(Cue(index=len(cues), page=page, text=line))
    return cues


def extract_pdf_text(pdf_path: Path) -> str:
    """Return concatenated text of all pages of the PDF."""
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
```

**Step 4: Run test — confirm it passes**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_script.py -v
```

**Expected:** PASS — 4 tests

**Step 5:** (skip commit — no git repo)

---

## Task 2: Chunker (`core/chunker.py`)

**Files:**
- Create: `core/chunker.py`
- Test: `tests/test_chunker.py`

**Step 1: Write the failing test** — `tests/test_chunker.py`

```python
from core.chunker import group_shots


def _shot(sid, sp, ep):
    return {"shot_id": sid, "start_pts": sp, "end_pts": ep}


def _labels(shots, location, chars):
    return {s["shot_id"]: {"location": location, "characters": chars} for s in shots}


def test_empty():
    assert group_shots([], {}) == []


def test_three_contiguous_shots_form_one_chunk():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200), _shot("shot:3", 200, 300)]
    labels = _labels(shots, "forest", ["Teegra"])
    chunks = group_shots(shots, labels)
    assert len(chunks) == 1
    assert chunks[0].shot_ids == ["shot:1", "shot:2", "shot:3"]


def test_four_shots_cap_at_three():
    shots = [_shot(f"shot:{i}", i * 100, (i + 1) * 100) for i in range(1, 5)]
    labels = _labels(shots, "forest", ["Teegra"])
    chunks = group_shots(shots, labels)
    assert [c.shot_ids for c in chunks] == [["shot:1", "shot:2", "shot:3"], ["shot:4"]]


def test_location_change_splits():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    labels = {
        "shot:1": {"location": "forest", "characters": ["Teegra"]},
        "shot:2": {"location": "castle", "characters": ["Teegra"]},
    }
    assert len(group_shots(shots, labels)) == 2


def test_character_set_change_splits():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    labels = {
        "shot:1": {"location": "forest", "characters": ["Teegra"]},
        "shot:2": {"location": "forest", "characters": ["Larn"]},
    }
    assert len(group_shots(shots, labels)) == 2


def test_empty_labels_do_not_split():
    shots = [_shot("shot:1", 0, 100), _shot("shot:2", 100, 200)]
    assert len(group_shots(shots, {})) == 1
```

**Step 2: Run test — confirm it fails**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_chunker.py -v
```

**Expected:** FAIL — `ModuleNotFoundError: No module named 'core.chunker'`

**Step 3: Write minimal implementation** — `core/chunker.py`

```python
"""Group adjacent shots into 2-3 shot chunks by visual continuity.

A chunk continues while the next shot shares the same location AND the
same character set (within overlap tolerance). Hard cap: 3 shots per chunk.
A shot flanked by discontinuities on both sides becomes a 1-shot chunk.
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
            id=f"chunk:{i:05d}",
            shot_ids=[s["shot_id"] for s in g],
            start_pts=first["start_pts"],
            end_pts=last["end_pts"],
            location=lab["location"],
            characters=lab["characters"],
        ))
    return chunks
```

**Step 4: Run test — confirm it passes**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_chunker.py -v
```

**Expected:** PASS — 6 tests

**Step 5:** (skip commit — no git repo)

---

## Task 3: Chunk audio extractor (`core/chunk_audio.py`)

**Files:**
- Create: `core/chunk_audio.py`
- Test: `tests/test_chunk_audio.py`

**Step 1: Write the failing test** — `tests/test_chunk_audio.py`

```python
from pathlib import Path

from core.chunk_audio import build_command, pts_to_seconds


def test_pts_to_seconds():
    assert pts_to_seconds(24000) == 1.0
    assert pts_to_seconds(0) == 0.0
    assert pts_to_seconds(12000) == 0.5


def test_build_command_structure():
    cmd = build_command(Path("audio/master.wav"), 0, 24000, Path("out.wav"))
    assert cmd[0] == "ffmpeg"
    assert "-ss" in cmd
    assert cmd[cmd.index("-ss") + 1] == "0.000000000"
    assert "-t" in cmd
    assert cmd[cmd.index("-t") + 1] == "1.000000000"
    assert "-ar" in cmd and "48000" in cmd
    assert "-ac" in cmd and "2" in cmd
    assert cmd[-1] == "out.wav"


def test_build_command_duration():
    cmd = build_command(Path("audio/master.wav"), 12000, 36000, Path("out.wav"))
    assert cmd[cmd.index("-ss") + 1] == "0.500000000"
    assert cmd[cmd.index("-t") + 1] == "1.000000000"
```

**Step 2: Run test — confirm it fails**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_chunk_audio.py -v
```

**Expected:** FAIL — `ModuleNotFoundError: No module named 'core.chunk_audio'`

**Step 3: Write minimal implementation** — `core/chunk_audio.py`

```python
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
```

**Step 4: Run test — confirm it passes**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_chunk_audio.py -v
```

**Expected:** PASS — 3 tests

**Step 5:** (skip commit — no git repo)

---

## Task 4: ASR wrapper (`core/asr.py`)

**Files:**
- Create: `core/asr.py`
- Test: `tests/test_asr.py`

**Step 1: Write the failing test** — `tests/test_asr.py`

```python
from core.asr import segments_to_records


class _FakeSeg:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


def test_segments_to_records():
    segs = [_FakeSeg(0.0, 1.5, "  hello  "), _FakeSeg(1.5, 3.0, "world")]
    recs = segments_to_records(segs)
    assert recs[0] == {"index": 0, "start": 0.0, "end": 1.5, "text": "hello"}
    assert recs[1] == {"index": 1, "start": 1.5, "end": 3.0, "text": "world"}


def test_empty_segments():
    assert segments_to_records([]) == []
```

**Step 2: Run test — confirm it fails**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_asr.py -v
```

**Expected:** FAIL — `ModuleNotFoundError: No module named 'core.asr'`

**Step 3: Write minimal implementation** — `core/asr.py`

```python
"""Transcribe master audio with faster-whisper (local GPU)."""
from __future__ import annotations

from pathlib import Path


def segments_to_records(segments) -> list[dict]:
    """Serialize faster-whisper segments to plain dicts. Pure."""
    return [
        {"index": i, "start": round(float(s.start), 3),
         "end": round(float(s.end), 3), "text": str(s.text).strip()}
        for i, s in enumerate(segments)
    ]


def transcribe(wav_path: Path, model_size: str = "large-v3",
               device: str = "cuda", compute_type: str = "float16") -> list[dict]:
    """Transcribe a WAV and return timecoded segment records.

    First run downloads the whisper model (~3 GB) to the local cache.
    """
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(str(wav_path), word_timestamps=True)
    return segments_to_records(segments)
```

**Step 4: Run test — confirm it passes**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_asr.py -v
```

**Expected:** PASS — 2 tests

**Step 5:** (skip commit — no git repo)

---

## Task 5: VLM correlation wrapper (`core/vlm_correlate.py`)

**Files:**
- Create: `core/vlm_correlate.py`
- Test: `tests/test_vlm_correlate.py`

**Step 1: Write the failing test** — `tests/test_vlm_correlate.py`

```python
import base64

import pytest
from pydantic import ValidationError

from core.vlm_correlate import build_prompt, encode_image, validate_output


def test_valid_output_passes():
    raw = {"scene_id": "s1", "location": "forest", "shots": [
        {"shot_id": "shot:1", "characters": ["Teegra"], "action": "talking", "confidence": 0.9}
    ]}
    out = validate_output(raw)
    assert out.location == "forest"
    assert out.shots[0].characters == ["Teegra"]


def test_invalid_confidence_rejected():
    raw = {"scene_id": "s1", "location": "forest", "shots": [
        {"shot_id": "shot:1", "confidence": 2.0}
    ]}
    with pytest.raises(ValidationError):
        validate_output(raw)


def test_missing_shot_id_rejected():
    raw = {"scene_id": "s1", "location": "forest", "shots": [{"characters": []}]}
    with pytest.raises(ValidationError):
        validate_output(raw)


def test_prompt_contains_shots_and_script():
    p = build_prompt("SCRIPT TEXT", ["shot:1", "shot:2"])
    assert "shot:1" in p and "shot:2" in p and "SCRIPT TEXT" in p


def test_encode_image_roundtrip(tmp_path):
    img = tmp_path / "a.jpg"
    img.write_bytes(b"\xff\xd8\xff\xd9")
    assert base64.b64decode(encode_image(img)) == b"\xff\xd8\xff\xd9"
```

**Step 2: Run test — confirm it fails**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_vlm_correlate.py -v
```

**Expected:** FAIL — `ModuleNotFoundError: No module named 'core.vlm_correlate'`

**Step 3: Write minimal implementation** — `core/vlm_correlate.py`

```python
"""VLM correlation: stills + script -> structured shot labels via Qwen3-VL.

Runs against LM Studio's OpenAI-compatible endpoint. The model returns JSON;
we validate it against a Pydantic schema before it is trusted downstream.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

from pydantic import BaseModel, Field


class ShotLabel(BaseModel):
    shot_id: str
    characters: list[str] = Field(default_factory=list)
    action: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class CorrelationOutput(BaseModel):
    scene_id: str
    location: str
    shots: list[ShotLabel]
    dialogue_assignments: list[dict] = Field(default_factory=list)


def validate_output(raw: dict) -> CorrelationOutput:
    """Validate VLM JSON against the correlation schema. Raises on bad input."""
    return CorrelationOutput.model_validate(raw)


def encode_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_prompt(script_span: str, shot_ids: list[str]) -> str:
    shots = "\n".join(shot_ids)
    return (
        "You are a film analyst. Given the stills of the shots listed below, in "
        "order, plus the script excerpt, produce JSON with:\n"
        "- scene_id and location (the environment shown)\n"
        "- per-shot: shot_id, characters present (named from the script), coarse "
        "action, confidence 0.0-1.0\n"
        "- dialogue_assignments: which script lines fall in which shot\n\n"
        f"Shots (in order):\n{shots}\n\n"
        f"Script excerpt:\n{script_span}\n\n"
        "Respond with ONLY the JSON, no prose."
    )


def call_vlm(model: str, prompt: str, image_paths: list[Path],
             base_url: str = "http://127.0.0.1:1234/v1") -> dict:
    """Send one multimodal request to LM Studio and return the parsed JSON."""
    import requests
    content = [{"type": "text", "text": prompt}]
    for p in image_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{encode_image(p)}"},
        })
    resp = requests.post(
        f"{base_url}/chat/completions",
        json={"model": model, "messages": [{"role": "user", "content": content}],
              "temperature": 0.2},
        timeout=600,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)
```

**Step 4: Run test — confirm it passes**

```bash
cd /e/FNI && .venv/Scripts/python.exe -m pytest tests/test_vlm_correlate.py -v
```

**Expected:** PASS — 5 tests

**Step 5:** (skip commit — no git repo)

---

## Task 6: Integration — first-window qualification (NOT TDD)

This task exercises every module against real data on the first 10-minute window and proves the pipeline before the full film runs. It is qualification, not unit testing.

**Files:**
- Create: `run_stage2.py` (orchestrator CLI)

**Step 1: Script extraction**

```bash
cd /e/FNI && .venv/Scripts/python.exe -c "
from core.script import extract_pdf_text, parse_script
from pathlib import Path
text = extract_pdf_text(Path('docs/doc.pdf'))
cues = parse_script(text)
print(f'{len(cues)} cues extracted')
print('first 3:', [c.text[:60] for c in cues[:3]])
print('last 1:', cues[-1].text[:60])
"
```

**Expected:** a sane cue count (tens, not hundreds), page numbers present. The text is the Scripts.com transcript.

**Step 2: ASR on a slice (not the full film)**

```bash
cd /e/FNI && .venv/Scripts/python.exe -c "
from core.asr import transcribe
from pathlib import Path
recs = transcribe(Path('audio/stems/m000_010/shot_00001.wav'))
for r in recs[:10]:
    print(f\"{r['start']}-{r['end']}: {r['text']}\")
"
```

**Expected:** timestamped text, with the whisper model downloaded on first run. Do this on a single stem first — it validates the wrapper without an 81-minute job.

**Step 3: VLM labeling on one shot (3 stills)**

```bash
cd /e/FNI && .venv/Scripts/python.exe -c "
from core.vlm_correlate import call_vlm, validate_output
from pathlib import Path
model = 'qwen3-vl-8b-instruct-abliterated-v2.0@f16'
imgs = sorted(Path('stills/full').glob('shot_00001_f*.jpg'))
prompt = 'You are a film analyst. Describe the character(s) and location in these stills as JSON: {\"location\": \"\", \"characters\": [], \"action\": \"\", \"confidence\": 0.0}'
print(call_vlm(model, prompt, imgs[:3]))
"
```

**Expected:** a JSON dict back from LM Studio. This proves the multimodal call works end to end. If LM Studio rejects image content, this is where it surfaces — stop and report rather than papering over.

**Step 4: Chunk the first window**

```bash
cd /e/FNI && .venv/Scripts/python.exe -c "
import json
from core.chunker import group_shots
shots = [json.loads(l) for l in open('shots.jsonl', encoding='utf-8')]
cut = 600 * 24000
window = [s for s in shots if s['start_pts'] < cut]
# labels are empty for now — chunker degrades to 3-shot max grouping
chunks = group_shots(window, {})
print(f'{len(window)} shots -> {len(chunks)} chunks')
print('chunk sizes:', [len(c.shot_ids) for c in chunks[:10]])
"
```

**Expected:** 111 shots → ~37 chunks (3-per-chunk cap), first chunk = shots 1–3.

**Step 5: Extract one chunk's audio + verify**

```bash
cd /e/FNI && .venv/Scripts/python.exe -c "
import json
from core.chunker import group_shots
from core.chunk_audio import extract_chunk_audio
from pathlib import Path
shots = [json.loads(l) for l in open('shots.jsonl', encoding='utf-8')]
cut = 600 * 24000
window = [s for s in shots if s['start_pts'] < cut]
chunks = group_shots(window, {})
c = chunks[0]
out = Path('audio/chunks') / (c.id + '.wav')
out.parent.mkdir(parents=True, exist_ok=True)
extract_chunk_audio(Path('audio/master_audio_48k_stereo.wav'), c.start_pts, c.end_pts, out)
print(out, out.stat().st_size)
"
```

**Expected:** a WAV whose size ≈ `(end_pts - start_pts) / 24000 * 48000 * 2 * 2` bytes (48kHz × 16-bit × stereo). Verify by comparing to that formula.

**Step 6: Report**

After all five steps, report: cue count, ASR output quality on the stem, VLM JSON shape, chunk count for the window, chunk audio size vs expected. Flag anything that deviates — this is the qualification gate before scaling to the full film.

---

## Open questions carried into execution

- **ASR ↔ script alignment for speaker attribution** is deferred. Task 6 Step 2 gives the first data to judge how well they agree. Do not build the aligner until that evidence is in hand.
- **VLM identity confidence at 8B** — Task 6 Step 3 shows whether fine character identity is reliable enough, or whether a confirmation loop is needed.
