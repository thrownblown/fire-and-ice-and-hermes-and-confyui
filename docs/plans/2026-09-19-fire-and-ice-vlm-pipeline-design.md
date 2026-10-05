# Fire & Ice — Script Parsing + VLM Correlation + Chunking (Stage 2) — Design

**Date:** 2026-09-19
**Status:** design (awaiting approval before implementation)
**Authority:** superpowers workflow — brainstorm → design → plan → build

---

## Decisions (settled in brainstorm)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Generation mode | Ref2V with **forced Bakshi audio** (`reference_audio` / `<Audio N>`). No V2V. No FFLF. |
| 2 | Chunking | **2–3 shots per chunk**, ~10s H3 render target. **Visual continuity drives grouping.** |
| 3 | Script parsing | **VLM (Qwen3-VL-8B) structures the script jointly with stills** → scenes, characters, dialogue↔shot mapping. Not a pure text parser. |
| 4 | Dialogue alignment | No subtitle track in the rip → **ASR (faster-whisper) on the extracted 940 MB WAV**, aligned to the script text later. |
| 5 | Prompt writing | Separate creative pass with a larger text model (qwq-32b / gemma-4-26b). **Out of scope for this build.** |

**Open question (carried forward, not blocking):** whether to align ASR output to the script for speaker attribution, or use ASR text alone. Decided by inspecting ASR-vs-script agreement on the first window — do not pre-commit.

---

## Architecture overview

Stage 1 (already done) produced the source substrate: 1308 frame-exact cuts, 3924 first/median/last stills, per-shot stems, and a continuous 940 MB master audio track.

This build is **Stage 2: correlation + chunking.** It turns that substrate plus the script into structured, chunked units ready for H3 prompt generation. The H3 prompt writer is a downstream consumer, named here but not built here.

Two inputs, one joint model pass, three outputs:

```
  stills (time order)  ─┐
                        ├─► VLM correlation pass ─►  scenes / characters / per-shot labels / dialogue↔shot map
  script (narrative)   ─┘                                        │
                                                                 ▼
                                            chunker (2–3 shots, visual continuity)
                                                                 │
                                                                 ▼
                                   chunk manifest  +  cue joins  +  per-chunk audio stems
```

The VLM pass is **windowed** — it never sees the whole film at once. It runs per candidate scene or per chunk, bounded by the v0.3 policy limits (`evidence_thumbnails_max: 8`, `text_token_target: 4000`).

---

## Components and responsibilities

### 1. Script extractor (`core/script.py`)
- Reads `docs/doc.pdf` (text layer already present).
- Splits the 10-page transcript into **cue candidates**: line text, page, order.
- Speaker attribution is **not** done here — the script is mostly running dialogue with only partial speaker marks. Attribution comes from the VLM pass and the ASR↔script alignment.
- Output: ordered list of raw cue candidates, no timecodes.

### 2. ASR transcriber (`core/asr.py`)
- Runs faster-whisper locally on the 5090 against `audio/master_audio_48k_stereo.wav`.
- Produces **timecoded segments** (text + start/end time + confidence).
- Word-level timestamps preferred; segment-level acceptable for v1.
- No speaker diarization in v1 — speaker identity comes from the script alignment, not from audio analysis.

### 3. VLM correlation pass (`core/vlm_correlate.py`)
- Model: `qwen3-vl-8b-instruct-abliterated-v2.0@f16` via LM Studio (`http://127.0.0.1:1234/v1`).
- Input (per window): the window's stills (first/median/last per shot) + the corresponding script span + the ASR segments in that time range.
- Output (structured JSON):
  - **scene boundaries** (location changes inferred from stills)
  - **per-shot labels**: characters present, location, coarse action
  - **dialogue↔shot mapping**: which script/ASR lines fall in which shot
- Emits **confidence** per label; identity ambiguity is flagged, not guessed.

### 4. Chunker (`core/chunker.py`)
- Deterministic, no LLM.
- Groups 2–3 adjacent shots into a chunk by **visual continuity**: same location + same character set + no hard scene change.
- Target: chunk's generated duration ≈ 10s (H3 renders the multi-shot sequence; keep-window trims).
- Output: chunk manifest — chunk ID, member shot IDs, time range, aligned frame count.

### 5. Audio stemmer (`core/chunk_audio.py`)
- Extracts each chunk's audio span from the **continuous** master WAV (never concatenates stems — see v0.3).
- Output: `chunk_XXXX.wav` per chunk = the `reference_audio` payload for H3.

### 6. (Downstream, not built here) H3 prompt writer
- Takes the chunk manifest + labels + dialogue + reference bindings.
- Emits the 6-section ref2v prompt. Uses a larger text model.

---

## Data flow

```
doc.pdf ──► script.py ──► cue candidates ──────────────────┐
                                                           │
master.wav ──► asr.py ──► timecoded segments ──────────────┤
                                                           │
stills/*.jpg ───────────────────────────┐                  │
                                         ▼                  ▼
                              vlm_correlate.py  (windowed, joint)
                                         │
                                         ▼
                     scenes + per-shot labels + dialogue↔shot map
                                         │
                                         ▼
                                   chunker.py
                                         │
                                         ▼
                       chunk manifest + cue joins
                                         │
                                         ▼
                                   chunk_audio.py
                                         │
                                         ▼
                          chunk_XXXX.wav (reference_audio)
```

All intermediates are JSON on disk. Each component is independently re-runnable and skips completed outputs (same resumability discipline as Stage 1).

---

## Error handling approach

- **VLM uncertainty is first-class.** Every label carries a confidence and a `needs_review` flag. Ambiguous identity (Larn vs a subhuman, etc.) goes to a human review queue, not silently into the chunk.
- **ASR noise is expected.** Raw ASR is kept alongside the script-aligned version. Where ASR and script disagree, the discrepancy is recorded, not resolved by fiat. Alignment failures are surfaced, not papered over.
- **Blank stills are pre-flagged** from Stage 1 (8 known). The VLM pass skips them rather than inferring from black frames.
- **Loud failure over silent corruption** (carried from Stage 1): every component exits non-zero and names the offending shot/chunk on failure. Counts are verified against the manifest before success is reported.
- **Idempotency:** re-running any component reproduces or skips, never duplicates.

---

## Testing strategy

- **Deterministic components (script.py, chunker.py, chunk_audio.py):** TDD — failing test → implement → green → commit. Pure functions where possible (chunk grouping, audio span math) so tests are fast and exact.
- **VLM pass:** cannot be unit-tested. Qualified on the **first 10-minute window** with a bounded golden set — hand-check ~20 labelled shots for scene/character correctness before trusting the pass on the full film. 8B at the low end for fine identity; confirm it on real stills before scaling.
- **ASR↔script alignment:** tested on the first window by inspection — does the aligned output make narrative sense? Decision point for the carried open question.
- **Round-trip integrity:** chunk audio spans must reconstruct from the master WAV within a sample-count tolerance, verified against the chunk manifest (mirrors the Stage 1 frame-count fidelity check).
- **End-to-end slice:** one 2–3 shot chunk flows through all components and yields a well-formed chunk package before the full film runs.

---

## Scope boundaries

**In scope:** script extraction, ASR transcription, VLM correlation, chunking, per-chunk audio stems.

**Out of scope (downstream):** H3 prompt text generation, actual rendering, lip-sync/post pass, assembly. The 124-frame H3 floor interaction is handled by the chunker's ~10s target, but its tuning is a render-stage concern.
