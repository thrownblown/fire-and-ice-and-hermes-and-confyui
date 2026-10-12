# Workstreams — parallel prep for the RefMod/asset build

*2026-10-12. The 5090 is offline, so split the work into (a) GPU-free prep that can run
now in parallel and (b) a 5090 return queue. Alex owns the watch-verdicts; short-lived
agents own the mechanical prep. Everything keys to existing ledgers — no new ledgers.*

## The two open questions (with a lean, to be settled by test not argument)

**Q1 — Are the H3 character sheets (multi-panel "circles") good enough as identity refs?**
Lean: workable as the *floor*, not the ceiling. The known risk is panel misreading — H3
treats panels as different people unless the prompt carries the "same person, multiple
views" line, and over-describing panels hurts. The 23 existing sheets are un-verdict'd;
verdict them (WS-2) before assuming they're usable.

**Q2 — Is it worth doing RefMods (vs just sheets as refs)?**
Lean: worth ONE cheap pilot to decide. The win is identity + voice baked into a single
`.refmod` file reused across all shots (no per-shot re-description); the cost is the create
step and the single-face constraint (two faces collapse into clones). Pilot = bake one
character, A/B refmod vs sheet on the same shot + seed. Recipe is in the fni-h3-pipeline skill.

## Workstreams

### WS-1 — Voice library + audio-plan decision (no GPU, unblocked now)
Owner: Alex (picks) + agent (cuts).
1. Alex ticks 3–5 clean lines per character in `audio/voice-review.md`, totaling ~20–30s
   each (NOT 4s clips — the RefMod create node's ceiling is 30s / 5120 tokens).
2. Agent cuts picks to `library/voice/<CHAR>_ref.wav` (ffmpeg, off `audio/lines/`).
3. Alex audits T0008 (original stems over S03) → decides audio plan A vs B/C. If A wins,
   voice refs drop off the critical path for dialogue scenes (but still needed for new lines).
Output: `library/voice/` populated + audio-plan verdict.

### WS-2 — Character identity lock + RefMod pilot
Owner: Alex (verdicts) + agent (descriptor drafts) + 5090 (pilot render).
1. Alex verdicts the 23 existing sheets (Juliana 7, Nekron 7, Darkwolf 9, Teegra v01).
2. Lock remaining descriptors: Teegra (earring/pendant/skin/body), Roliel (confirm),
   Tutor (none yet). Agent drafts from corpus stills via LM Studio `qwen3-vl-8b`; Alex signs.
3. RefMod pilot (queued for 5090): bake one character via `H3RefModCreateFromFolder`,
   A/B refmod vs approved sheet on the same shot + seed. Watch → verdict settles Q2.
Output: signed descriptor + approved sheet + refmod-vs-sheet verdict.

### WS-3 — Visual assets: backgrounds + Frazetta restyle + style LoRA
Owner: agent (curation) + 5090/edit model (generation).
1. Curate plan-A comic LoRA dataset (no GPU): 20–40 stills from `stills/full/`, style-only
   captions. Free, unblocked.
2. Enumerate ~15 canonical location plates + per-setup background requirements from the beat
   sheet (`docs/01-roster.md` locations, `manifests/continuity_v2.jsonl` setups). No GPU.
3. Generation (queued): Frazetta-restyle approved sheets + location plates (edit model), then
   train comic LoRA, then painting LoRA after restyle assets land.
Output: comic LoRA + location plates + Frazetta-styled sheets (plan-B dataset).

### WS-4 — Backgrounds at scale (setup plates)
Owner: blocked on T0011/T0012 verdicts + 5090.
1. Decide per-setup vs per-shot plate strategy (the skill already leans per-shot + shared
   plate for dialogue-heavy setups).
2. Generate master background plates per setup once T0011/T0012 land and 5090 returns.
Output: `refs/setups/{tag}_plate.jpg` for all setups (currently only S06 pilot exists).

## 5090 return queue (ordered)

1. Pull T0011/T0012 outputs (`tools/pull_5090.py`) → Alex verdicts them → unblocks T0013/T0014.
2. RefMod pilot render (WS-2.3).
3. Comic LoRA training (WS-3, dataset already curated).
4. Location/setup plate generation (WS-4).
5. Frazetta restyle pass → painting LoRA (plan B).

## Parallelism

Now (5090 offline): WS-1, WS-2.1/2.2, WS-3.1/3.2 all run concurrently — audio cuts, descriptor
drafts, sheet verdicts, and style/location curation are independent and GPU-free. Alex's watch
queue (sheets, voice picks, T0008) is the only serial bottleneck.
