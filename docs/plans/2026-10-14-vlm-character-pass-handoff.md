# Handoff — Multi-lens VLM character pass (restart with fresh context)

Date: 2026-10-14. Status: DONE 2026-10-14 (main session, no delegation). Tasks 1-3 built TDD
(142 tests green), smoke 5/5 grounded, full batch 1,120/1,120 calls ok (0 failures, ~65 min),
all 14 profiles synthesized to library/char/profiles/. Ledger: manifests/vlm_charpass.jsonl
(1,121 rows incl. smoke). Fix applied mid-run: nullish strings ("null"/"None"/"N/A") from the
VLM normalized to null (core + synth filters). Previous delegation stalled; nothing had landed.

## Read first (authoritative — do not re-derive)

- `docs/plans/2026-10-13-vlm-character-pass.md`        (task breakdown + contracts)
- `docs/plans/2026-10-13-vlm-character-pass-design.md` (lenses, schemas, storage, aggregation)
- `tools/vlm_traits.py`                                 (existing LM Studio vision-call + PIL `encode_image` pattern — match it)

## Goal

Build the multi-lens VLM character-pass pipeline: many cheap per-image VLM calls across
`refs/characters/<NAME>/`, each with a narrow system prompt (lens) and strict JSON, cached,
then deterministic majority-vote aggregation into per-character profiles with a
`prompt_block` for Krea 2 stills prompts.

Files to build (TDD mandatory — failing test first, pytest in `E:\FNI\.venv`):

- Task 1: `core/vlm_charpass.py` (pure library) + `tests/test_vlm_charpass.py`
- Task 2: `tools/vlm_character_pass.py` (runner, injectable fake transport) + tests
- Task 3: `tools/vlm_profile_synth.py` (aggregation, fixture ledger) + tests
- Task 4: integration smoke — run by the parent, NOT a subagent (5 real calls, then the full batch as a background terminal job)

## Why the previous attempt stalled (avoid this)

Delegation `deleg_04611dd4` (2 subagents: core+runner, and synth) ran ~2.9 h on 2026-10-14,
read only the context files, wrote NOTHING to disk, and was stopped. Root cause:

1. Delegated model `qwen3.8-27b-heretic` (local 27B on LM Studio) is crash-prone/slow —
   it hung between tool calls (idle gaps of 70 min and 2 h in the live transcripts).
2. TWO subagents were fanned out on the single 4090 LM Studio/GPU at once → contention.
   (Known FNI rule: don't fan out local subagents; single GPU → stalls / "too large".)

## Recommended execution for the fresh run

- Do NOT delegate this to the local 27B, and do NOT run two subagents on LM Studio at once.
- Best: build it in the main session directly (fast, reliable), one task at a time:
  Task 1 → Task 2 → Task 3 → Task 4 smoke.
- If you must delegate: ONE subagent at a time, pinned to a faster loaded model
  (`qwen3.8-flash-next@bf16` is loaded on LM Studio and far quicker than the 27B) — not the heretic 27B.

## Contracts (every task honors these)

- LM Studio: POST `http://127.0.0.1:1234/v1/chat/completions`, model
  `qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s` (vision; `--model` override). Serial calls,
  one at a time. Retry ladder on HTTP 400/429/5xx/timeout: 3 attempts, temp 0.0->0.5,
  max_tokens 600->900, 3 s sleep between.
- Images: JPEG downscale, long edge 1024 default (reuse `encode_image` in `tools/vlm_traits.py`).
- Cache key: (char, lens, image basename, mtime, size, model). A cached row is never re-queried.
- Ledger `manifests/vlm_charpass.jsonl` (append-only), one row per call:
  `{"ts","char","lens","image","model","ok","attempts","text"(raw),"json"(normalized|null)}`.
  Normalization failures keep the raw text and set `json=null` — never throw away an answer.
- Forward slashes in JSON machine paths.

## Lenses (7) — schema + instruction text per the design doc

    physique  {sex, age_range, build, height_impression, skin_neutral_light}
    face      {face_shape, eyes, brows, nose, lips, distinguishing_features[]}
    hair      {color, length, texture, style, notes}
    wardrobe  {garments: [{item, color, material, cut}], state_of_dress}
    props     {items: [{item, color, worn_or_carried, body_location}], weapons[]}
    colors    {skin, hair, eyes, garment_primary, garment_secondary, metal_accent}
    signature {memorable_traits[], unmistakable_because}

System-prompt invariants: describe only what is visible; never name characters/actors;
skin in neutral light (ignore colored scene lighting); strict JSON only, no prose/fences;
one frame per call.

## Aggregation

`consensus(values) -> {"value","share","n","outliers"}`: lowercase-collapse, substring-merge
(e.g. "long black" in "long, straight, black hair"), majority vote. Stable = share >= 0.6.
Deterministic, NO LLM. Profile sections: stable traits, disputed traits, and a
`prompt_block` paragraph (composed specific description for Krea 2 prompts).

## Storage

    library/char/vlm-cache/<CHAR>/<lens>/<image>.json   per-call cache (mtime/size/model keyed)
    manifests/vlm_charpass.jsonl                        append-only run ledger
    library/char/profiles/<CHAR>.json + <CHAR>.md       aggregated profile + human sheet

## Corpus

`refs/characters/<NAME>/` — 14 dirs: TEEGRA 24, ROLIEL 28, DARKWOLF 16, LARN 12, TUTOR 9,
SHAITAN 7, NEKRON, JAROL, JULIANNA, OTWA, SPIRIT, SUBHUMAN, SUBHUMAN CAPTAIN, SUBHUMAN LEADER.
(Solo-shot stills extension from `stills/full/` is a LATER task — corpus = `refs/characters` only for now.
Named solo-shot volume for later: Teegra 142, Larn 82, Nekron 65 shots.)

## Rules

- TDD: failing test first, then implement. Run: `E:\FNI\.venv\Scripts\python.exe -m pytest`.
- No git commits (only the user commits).
- The 5090 ALSO generates image stills (Krea2, e.g. the Teegra workflow) — it is NOT H3-only.
  The Teegra still workflow lives at `Downloads/ComfyUI_00108_.json` and runs fine on the 5090;
  tune only the prompt and LoRA strengths. Drive it with `tools/krea2_stills.py`.
