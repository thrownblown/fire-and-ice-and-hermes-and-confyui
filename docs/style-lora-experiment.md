# T0006/T0007 — Fire & Ice style-LoRA experiment (two plans)

*Drafted 2026-10-01. Two mutually-exclusive LoRA targets, drafted separately so one
can be picked or both run back-to-back. Same training mechanics both ways; the
dataset and the eval question differ.*

---

## Director's own words (fatal reframe)

From Ralph Bakshi's audio commentary: he wanted **Frank Frazetta's comic style,
not the painting style, "as that would be impossible"** with rotoscope — and "now
we could just do it all with computers."

This splits "the look" into three, not two:

1. **Comic/ink style** — Frazetta's line-and-flat-color illustration work. This is
   what the 1983 film actually IS: rotoscoped cels, black ink outlines, flat
   painted fills. It was the achievable approximation, not the ideal.
2. **Painting style** — the fully-rendered oil-painting look (Frazetta's rendered
   covers/Death Dealer). This is what Bakshi *wanted* and said was impossible with
   rotoscope — and that he explicitly would do now with computers.
3. (The 2026 project's own layer on top of both: whatever H3 + refmods produce.)

So the A/B split is not "faithful vs stylized." It is:

- **Plan A = comic style** — reconstruct the film as it exists. LoRA pressed from
  the actual 1983 cels. This is *reproduction fidelity*.
- **Plan B = painting style** — fulfill the look Bakshi said was impossible. LoRA
  pressed from Frazetta-oil-restyled assets. This is *realizing the unfulfilled
  version*.

Ralph's commentary is effectively a green light for B: the painting style isn't a
deviation, it's the vision the director named and said technology now permits. The
creative decision (reproduce vs fulfill) sits with Alex; the experiment mechanics
for either are identical below.

## Shared training mechanics (both plans)

Toolkit and flags are identical regardless of target style. All confirmed against
`AkaneTendo25/musubi-tuner` branch `minimax-h3` (docs/minimax_h3.md).

- **Toolkit:** Musubi-Tuner `minimax-h3` fork, on the 5090 (or 4090 via
  `--blocks_to_swap 48`).
- **Checkpoint:** FL2VA, pre-quantized `minimax_h3_fl2va_pruned_int8_convrot.safetensors`
  (already on the 5090 staging disk) via `--int8_convrot_base --sdpa
  --mixed_precision bf16`.
- **Objective:** the doc's RECOMMENDED clean path — frozen training adapter
  `--h3_overlay_weights ... --h3_overlay_training_only`, plain flow-matching,
  guidance/preservation/rollout objectives OFF. Adapter: **Ostris v3**
  (`minimax_h3_training_adapter_v3.safetensors`) for FL2VA. Note the overlay is
  never merged into the saved LoRA; only the learned LoRA is loaded at inference.
- **LoRA targets (style only):** `--h3_lora_targets "attention;mlp"` — leave
  `audio` out; a style run has no reason to train the audio endpoints.
- **Rank/dim:** `--network_dim 8 --network_alpha 8` (matches the shipped working
  recipe). `--network_args nora=off` (default).
- **Optimizer/rate:** `--optimizer_type Automagic3 --learning_rate 1e-4
  --lr_scheduler constant --lr_warmup_steps 0`.
- **Environment:** `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (also set
  `PYTORCH_ALLOC_CONF` — some builds read only one).
- **Do not train audio.** No `--h3_audio_loss_weight`; keep the dataset
  video/image only so no noise fights the base audio.

**Cost/time (both):**
- ~1–2 hours standing up the fork + first cache (latents + text embeddings).
- ~20–30 min dataset curate.
- ~500 steps @ images-only ≈ well under an hour on the 5090 (0.6–0.7 s/step range
  per the Inline-Studio benchmarks; Musubi's guide is comparable ballpark).
- One eval comparison chunk = one FL2VA render (~1 s/frame), already measured.

Sequence: cache → train → save LoRA → infer a *comparison* chunk with and without
the LoRA → frame metrics + Alex watches → verdict.

---

## PLAN A — Faithful 1983 Bakshi (recommended first)

**Target:** the rotoscope cell-art look of the actual 1983 film — flat painted
cells, clean linework, high-contrast shapes, painterly backgrounds, the specific
Bakshi/Frazetta-designer papercut aesthetic.

**The question it answers:** "does a style LoRA pressed from the *original* film
lock the source look better than re-prompting the look on every chunk?"

### Dataset
- **Source:** `E:\FNI\stills\full\` — 3924 extracted frames from the master.
- **Curate (manual, 20–40 stills):** pick frames that are (a) unambiguously the
  film's style — no heavy motion blur, no hard cuts mid-frame, no captions/credits
  baked in — and (b) cover the visual spread: interior dark (Ice Peak/Fire Keep),
  exterior daylight (jungle, ice fields), close-ups and wide shots, both the
  painterly environment plates and the rotoscoped characters-on-cele.
- **Captions:** short, style-only sidecars (`NNNN.txt`). Describe the *rendering*,
  not the plot: "flat cel-shaded hand-painted animation still, black ink outlines,
  flat saturated color fills, painted matte background" — deliberately strip
  character/plot identity so the LoRA learns style, not subjects. Identity stays
  with refmods.
- **Resolution:** source stills at native res (they're film frames; use as-is or
  resize to a consistent training bucket, ~512–768px).

### Eval (the comparison that decides)
1. **Baseline:** one FL2VA chunk from an already-watched run (T0002/T0003
   material), same chunk + seed, re-rendered with the current prompt but **no
   LoRA**.
2. **LoRA-on:** same chunk + seed + prompt, LoRA loaded on the FL2VA graph.
3. **Frame metrics** (scripts/frame_metrics.py): anchor MSE, position profile,
   frozen fraction — the LoRA must not damage the structural-alive numbers the
   pipeline already fixed.
4. **Alex watches both** and answers one question: does the LoRA-on clip look
   *more like the 1983 film* than baseline, with no identity/motion regression?

### Verdict to record
- ✅ if LoRA-on reads as more "Fire & Ice" at equal or better structure.
- ❌ if it doesn't beat a well-prompted baseline — that means the look was already
  reachable by prompt, and the LoRA adds nothing worth the pipeline fork.

### Why A first
- Dataset is free (already on disk), zero style-transfer preprocessing.
- Purest test of "does a LoRA beat simply describing the style in the prompt."
- If it fails, it fails cheap and tells you refmods+prompt are sufficient; you
  don't then spend effort on Plan B's restyling layer.

---

## PLAN B — Frazetta-oil style transfer

**Target:** the restyled look from test-runs-plan.md layers 1–2 — source frames
pushed through an edit model into Frazetta oil-painting style, character sheets
and location plates as reusable style assets.

**The question it answers:** "does a LoRA trained on Frazetta-restyled assets carry
the oil-paint look into H3 motion, as a step toward the fuller chunk-pack
pipeline?"

### Dataset
- **Source:** the *outputs* of the style-transfer step (Frazetta-styled character
  sheets in `library/char/` + location plates in `library/loc/`), NOT the raw
  source stills. This plan depends on that restyle layer existing first — see the
  dependency below.
- **Curate (20–40):** the approved sheets and plates, plus any Frazetta-styled
  blocking frames that survived QA. Same style-only captioning discipline as A.
- **Resolution / bucket:** to match the 864×480 render target the pipeline already
  uses, if the sheets are produced at that size.

### Eval
Same baseline-vs-LoRA comparison as A, but the baseline prompt is the *Frazetta*
direction (sheets as refs), and the question is whether the LoRA adds coherence on
top of already-Frazetta-styled refs.

### Dependency / ordering
B cannot be run before the restyle layer produces a library of approved
Frazetta-styled sheets/plates. That layer is itself manual-ish work (10–15 char
sheets + ~15 plates). If A is run first, B picks up afterward using whatever the
restyle pass produced.

---

## Cross-cutting notes (both)

- **Refmods stay for identity either way.** A style LoRA covers "the look";
  per-shot `<Picture N>` refs still carry "who" and "where." The two must compose,
  not compete — the eval explicitly watches for identity regression when the LoRA
  is loaded.
- **One variable per run.** LoRA on/off is the variable. Chunk, seed, prompt
  length, and graph are held constant against prior T#### runs.
- **No audio training, no audio in eval** — visuals only.
- **Failure modes to expect:** LoRA that softens contrast (distilled-field
  collapse if the adapter flags are wrong) or over-saturates. The adapter path is
  chosen specifically to hold contrast; if the clip comes out soft, the first
  thing to check is whether the overlay adapter was actually active.
- **Save artifacts to a run folder** `runs/T0006_style-lora-bakshi` /
  `runs/T0007_style-lora-frazetta` with manifest.md, the dataset list, the exact
  train command used, and the saved LoRA file + its metadata.

## Open items before execution
1. ~~Pick plan A vs B~~ → **DECIDED: do both.** Train the comic LoRA AND the
   painting LoRA; the eval becomes a three-way comparison (no-LoRA baseline vs
   comic vs painting) on the same chunk + seed. Both styles available as reusable
   adapters regardless of which the final film favors.
2. Confirm the Ostris v3 adapter + Musubi fork can be stood up on the 5090 (the
   only genuinely unproven step — the rest is known-good).
3. Confirm 20–40 stills is enough for a style lock vs needing clips (images-only
   is expected fine for style; clips only become necessary if we later train
   *motion* or *character*).

## Execution order (both tracks)

- **Track A (comic LoRA): unblocked now.** Dataset is free (3924 stills already
  on disk in `stills/full/`); only needs curation + captions. No restyle
  dependency. This is the near-term run.
- **Track B (painting LoRA): gated on the restyle pass.** Needs the Frazetta-oil
  character sheets + location plates produced first (the manual-ish edit-model
  layer). Cannot start until that library exists.
- Sequencing that makes both cheapest: run A end-to-end first (proves the fork +
  adapter + train-infer loop on the 5090 with zero restyle cost), then bring B in
  once the restyle assets land. The machinery is shared, so A de-risks B.