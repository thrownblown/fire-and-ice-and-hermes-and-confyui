# Design — Multi-lens VLM character pass ("accuracy by volume")

Date: 2026-10-13. Status: approved for build (Alex: "use more a accuracy by volume
approach... feed to the vlm using different system prompts to get a wholistic view
of each character. focus on the vlm pass while i move all the assets... to the 5090").
Gate note: brainstorm questions compressed to stated assumptions per Alex's standing
preference ("assumptions made, not questions asked"); corrections welcome mid-flight.

## Problem

Character prompts for the Krea 2 stills pipeline must be as specific as what the VLM
reports (Alex: "more specific like what the [vlm]s are giving us back"). One coarse
VLM pass (manifests/character_names.jsonl: sex/build/hair/skin/clothing) is too thin
and single-pass answers drift. Fix: many cheap VLM calls across a corpus, each with a
narrow system prompt (lens), then aggregate — stable traits survive volume, drift
shows up as disagreement.

## Corpus

- refs/characters/<NAME>/ — curated per-character stills, 13 characters
  (TEEGRA 24, ROLIEL 28, DARKWOLF 16, LARN 12, TUTOR 9, SHAITAN 7, ...).
- Solo-shot stills from stills/full/ where manifests/character_names.jsonl has the
  character named and count_men+count_women == 1 (single-figure frames only —
  the 8B merges figures in busy frames; see vlm-image-labeling skill).
  Named volume: Teegra 142, Larn 82, Nekron 65 shots.

## Options considered

A. Multi-lens per-image pass + deterministic aggregation (CHOSEN): ~7 lenses x
   corpus, strict JSON, cached per (image, lens, model), majority-vote consensus.
   Volume is the accuracy mechanism; reruns are free (cache).
B. One rich prompt per image + big synthesis (current tools/vlm_traits.py): fewer
   calls, but one prompt biases what gets reported; no per-trait stability signal.
C. Cloud vision_analyze: most accurate individually, but not local, not cheap at
   volume, and the local volume approach is the point (render host stays free).

## Design (A)

Lenses — each a fixed system prompt + strict-JSON schema, one (image, lens) per call:

  physique    {sex, age_range, build, height_impression, skin_neutral_light}
  face        {face_shape, eyes, brows, nose, lips, distinguishing_features[]}
  hair        {color, length, texture, style, notes}
  wardrobe    {garments: [{item, color, material, cut}], state_of_dress}
  props       {items: [{item, color, worn_or_carried, body_location}], weapons[]}
  colors      {skin, hair, eyes, garment_primary, garment_secondary, metal_accent}
  signature   {memorable_traits[], unmistakable_because}

Shared system-prompt invariants (from vlm-image-labeling skill): describe only what
is visible; never name characters/actors; skin in neutral light (ignore colored
scene lighting); strict JSON only, no prose/fences. One frame per call.

Storage:
  library/char/vlm-cache/<CHAR>/<lens>/<image>.json   per-call cache (mtime/size/model keyed)
  manifests/vlm_charpass.jsonl                        append-only run ledger (one row per call)
  library/char/profiles/<CHAR>.json + <CHAR>.md       aggregated profile + human sheet

Aggregation (deterministic, no LLM): normalize value strings, cluster per trait,
majority vote -> consensus + agreement ratio + outliers. Profile sections:
stable traits (>=60% share), disputed traits (all answers listed), and a
prompt_block — the composed, VLM-specific character description for Krea 2 prompts.

## Constraints

- LM Studio 127.0.0.1:1234, model qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s
  (fallback qwen3.8-27b-heretic). One request at a time; retry ladder 3 attempts
  (temp 0.0->0.5, tokens 600->900, 3s apart). Sequence calls, never fan out.
- Subagent code work runs on lmstudio 27B (delegation pinned) — same GPU. Build
  phase first, VLM batch after (or interleaved at one-call-at-a-time pace).
- TDD per superpowers: failing test first, then implement. pytest in E:\FNI\.venv.
- No git commits (repo convention: only the user commits).

## Non-goals

- No setup/camera grouping here (setups_v2 territory), no prompt compilation
  (refrun grammar), no touching the 5090 (Alex is moving assets there himself).
