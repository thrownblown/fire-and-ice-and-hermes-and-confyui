# Absorbed production lessons (konte + OpenCineAgent)

Higher-level findings from two external projects that both report successful local H3 results,
distilled against what FNI already does. Source reports: `explore/konte-mine.md`,
`explore/opencineagent-mine.md`. This file is decisions, not archaeology — each entry ends in what
FNI has already absorbed or still should.

## The convergent core

Three things the two projects independently converged on, which is a stronger signal than any
single recommendation:

1. Identity is anchored once and repeated verbatim.
2. "Verified" means measured — a check that cannot run is skipped, never passed.
3. The order of work exists to make a wrong turn cheap (plan/review before render, hardest shot
   first, keep every take).

FNI already does (1) as identity-as-traits with a roster that overrides the VLM, and (3) via the
deterministic-seed, hashed-source, resumable-ledger pipeline in fullrun.py.

## 1. Prompt contract validator

Finding: a prompt must be mechanically checked for well-formedness before it costs a GPU render.
OpenCineAgent ships `validate_video_prompt()` (unbalanced `<d>`, missing field, >130-char line,
>2 speakers); konte makes the structural fields a type error. Neither renders an unchecked prompt.

Absorbed: `validate_prompt()` added to fullrun.py, wrapped around both prompt-write sites
(`cmd_prompt` and `refresh_one` in `cmd_render`). Adapted to FNI's three-field
`integrated_multimodal_description` grammar — FNI emits multiple `[Shot N]`, so the source
project's "only [Shot 1]" rule is deliberately NOT carried over.

It is non-fatal (logs violations, renders anyway). First run over 494 prompts flagged 7 — three
"dialog >200 chars, split the shot" and three ">2 speakers" — exactly the class that would
otherwise waste a render. Flip to a hard stop by raising once it is trusted.

## 2. Measured QC (verified = measured; pass/fail/skipped)

Finding: both projects separate PASSED / FAILED / SKIPPED and never promote an un-runnable check
to pass. OpenCineAgent's critic has four cheap checks, all portable to FNI's local-model stack:

- motion: mean luma < 6 => black clip; mean frame-diff < 0.3 => frozen clip (12 grayscale frames).
- audio: RMS < -45 dBFS with dialogue present => near-silent.
- dialogue: faster-whisper transcript vs script line, SequenceMatcher ratio vs a threshold
  (SKIPPED when faster-whisper absent).
- identity: local VLM (qwen2.5vl via Ollama) compares 4 frames vs approved master portraits,
  JSON verdict {same_identity, deformed_face, deformed_hands, extra_people}.

Not yet absorbed. FNI's `collect` does frame metrics only. The motion + audio checks are ~40 lines
and use no new model; the dialogue and identity checks need faster-whisper and a VLM call. Lift the
motion/audio pair first — they catch black and frozen clips with zero dependency.

Known local-model mapping (FNI already serves these): VLM identity = qwen3-vl-8b;
dialogue = local faster-whisper or reuse the existing ASR pass.

## 3. Identity anchor discipline

Finding: one master portrait per character, human-approved once; every keyframe derives from it;
the identity block repeats verbatim in every prompt; `ref_image_size: max`; RefMod only when one
face is on screen (a RefMod pushes identity on the whole conditioning, so two faces become clones).

FNI maps this onto: keyframe stills + character roster traits + name stamps. Gaps worth closing,
in rough value order:

- `ref_image_size: max` — confirm FNI's graph uses it (not `match`). `match` scales references to
  render size and averages two faces into one.
- RefMod single-face rule — only attach a character RefMod where the shot has exactly one face.
- Identity anchors must be the same files across clips that share a character (regenerating per
  clip degrades identity by ~clip 6).

## 4. ComfyUI discipline (production notes worth keeping near the render code)

- Success = downloaded non-empty artifact, never exit code or queue state. FNI's `recover` already
  probes files by name — keep that as the source of truth, not /history (a reboot wipes it).
- One heavy job at a time; call `/free` between model-set changes. A video player open on the GPU
  is enough to OOM.
- `MiniMaxH3RefModExtract` is not an output node — a `PreviewAny` terminal triggers it.
- H3 length rungs are `5 + 17k` frames @24fps: render the next valid length and trim at assembly.

## 5. Honest ceiling (stated by both authors)

A full feature film, fully unattended, is not there yet in either project: "keeping faces, wardrobe
and space consistent across hundreds of shots still needs human review." FNI's 1300-shot remake is
up against that same wall. Neither repo tooling removes it — they just make the human review loop
cheap and recordable, which is what FNI's h3-prompt-review.html and shot-browser.html already do.

## What was deliberately NOT absorbed

- konte's orchestrator (pre-1.0, un-dogfooded at scale, runs Claude Code/Codex) — FNI's fullrun.py
  is the right shape for FNI.
- konte's six-field vs OpenCineAgent's three-field prompt grammar ambiguity — FNI's running graph
  uses the three-field form; the six-field form lives in `h3_prompt_template.md` and the seed-hunter
  test. Leave both, but do not let a new prompt drift between them without intent.