# H3 LoRA registry — what we have, what we want, what to test

Companion to `docs/h3_reddit_threads.md` and the skill's `references/community-wisdom.md`.
The rule from the community digest still governs: **a turbo/few-step LoRA must not be combined
with Spectrum/SOL attention** (deep-fried audio), and a style LoRA is a separate axis from a turbo
LoRA — they stack, but re-check audio when you stack them at strength.

---

## Wanted / testing

### MiniMax H3 — Forgotten World's "Retro Fantasy" (style)
- Civitai: `civitai.com/models/2988830` (Granddyser), version **3388934**, published 2026-10-07.
- **Two files in that version** (same size ~569 MB, both fp32):
  | file | fileId | sha256 |
  | --- | --- | --- |
  | `retro-fantasy.safetensors` | 3278075 | `27EF791C…02E9B` |
  | `retro-fantasy-step00003750.safetensors` | 3278858 | — |
- **State on the 5090 (checked 2026-10-13):** `h3/retro-fantasy-step00003750.safetensors` is
  **already there**. `h3/retro-fantasy.safetensors` (the other file of the same version) is NOT.
  `h3/retro-80s.safetensors` is also present — a different, older retro LoRA.
- Fetch the missing one: `bash tools/download_5090_models.sh lora-retro-fantasy`
  (verified end to end on 2026-10-13: 596,449,424 bytes, sha256 matches Civitai's).
- **Structure:** 601 tensors, all F32, keys are `lora_unet_blocks_N_attn_{qkv,out}_proj` and
  `lora_unet_blocks_N_mlp_{fc1,fc2}` — UNET-only, rank 32. No text-encoder keys, and no fl2va /
  ref2va distinction in the naming, so it is a plain DiT style LoRA: apply with
  `LoraLoaderModelOnly` (or a `LoraLoader` taking just the MODEL output).
- **Author's guidance:** trigger word `retr0Fantasy`, **optional** — the LoRA works without it.
  16:9 gives the most reliable results. He recommends driving it from a **start frame** rather than
  pure text-to-video (which points at FL2VA / I2VA, i.e. our Track B/C, more than REF2VA). Sampler
  and scheduler combinations change results noticeably; his settings are in the Civitai example
  posts and workflows are in the model's attachments. Explicitly experimental — "results can vary
  significantly depending on the prompt, sampler, LoRA strength".

### Technicolor / era "movie still" style LoRAs (ArsMachina) — for the 80s sword-and-sandals pivot
- **80s Fantasy Movie** — Civitai `civitai.com/models/2946830`, version **3337011**
  (`80sFantasyMovie_minimaxh3_3333584_epoch_10.safetensors`, 296 MB). Trigger
  `ArsMovieStill, 80s Fantasy Movie Still`. Strength **1.2**; **1.2–1.7 when stacked with a turbo
  LoRA** (turbo diminishes the style). Images-only style LoRA → best on FL2V / T2I→I2V, and the
  author's own recipe is *generate the first frame in Krea 2, then apply this at REF2V*.
- **30s Technicolor Movie** — Civitai `civitai.com/models/886686`, version **3339781**
  (`30sTechnicolorMovie_minimaxh3_3339408_epoch_10.safetensors`, 296 MB). Trigger
  `ArsMovieStill, movie still from a 1930s technicolor movie`. Strength 1.2 (same turbo caveat).
- Both are plain DiT style LoRAs (no fl2va/ref2va marker) → `LoraLoaderModelOnly`.
- Fetch on the box: `bash tools/download_5090_models.sh lora-technicolor`.
- Full stack (including the Krea 2 side, Qwen-Edit role, and the H3-vs-LTX call):
  `docs/technicolor-lora-stack.md`.

## Already on the 5090 and rated by the community
| LoRA | Why | Source |
| --- | --- | --- |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16` | what our pipeline currently uses (4 steps @ 1.0 — the measured-weak row) | LightX2V |
| `minimax_h3_ref2v_turbo_8step_v1.0_768p`, `minimax_h3_fl2v_turbo_4step_v1.2_768p`, `..._8step_v1.0` | the accelerations Lumibelle kept | LightX2V |
| `minimax_h3_fl2v_turbo_silver_dareties_comfy_pruned_v1` | from the 1x1g4mu thread | silveroxides |
| `MiniMax-H3-FL2VA-Acc-8Step`, `MiniMax-H3-Ref2VA-Acc-8Step` | ACC 8-step | Kijai |
| `minimax_h3_raven_streaming_lora_4nfe_preview` | 4-NFE streaming | community |

## Wanted, not yet on the 5090
| LoRA | Why | Source |
| --- | --- | --- |
| **Larry v4 step600 EMA** | the winner of Lumibelle's measured benchmark at 6 steps (31–34 % faster, judged good) — needs its node pack | `larryvrh/MiniMax-H3-Turbo-Lora` |
| **Kijai rank-reduced DMAD** (`minimax_h3_DMAD_4step_full_lora_avg_rank_39_bf16`) | fixes the shiny/plastic skin most turbo LoRAs cause, good from ~5 steps | `Kijai/MiniMax-H3-experimental` |
| **fal realism-people** (`h3-realism-people-t2v-i2v-r2v`) | cheap skin realism, part of the community refmod stack | `fal/MiniMax-H3-Realism-People-LoRA` |

All three are in `tools/download_5090_models.sh` (tier 1 / tier 2).

## Character Swap LoRA (Akatz Labs) — the third identity route

- `h3_character_swap_pro4500_1000.safetensors` (155 MB) — **REF2VA** DiT LoRA
  (`ss_base_model_version: minimax_h3_ref2va`, 416 tensors, ostris/ai-toolkit, step 1000).
  Swaps a foreground character in a source video for a `<Picture 1>` reference character,
  preserving video camera/framing/background/lighting and matching pose/scale/movement.
  No trigger word. Full recipe + the replace/preserve/match prompt contract + the
  `ref_image_size: match` tension: `docs/h3-character-swap-lora.md`.
- Author HF: `akatz-ai/MiniMax-H3-Character-Swap-LoRA`. Workflow: `MINIMAXA CHARACTER SWAP
  patreon (1).json`. This is a THIRD identity route beside (A) Krea→Qwen-Edit wardrobe and
  (B) H3 ref2va sheet-holding — and the strongest match yet for "transplant live-action
  Teegra over the 1983 rotoscope choreography."

## Testing notes
- Test one variable at a time with a fixed seed; a style LoRA changes the look, so compare against
  the same prompt without it.
- Turbo LoRAs change the output for the same seed even when off vs on — never use a turbo LoRA to
  "preview" a take you intend to reproduce at full steps.
- For the retro-fantasy style specifically: try it on a **plate** (Z-Image is a different model, so
  no — this is an H3 LoRA) and on a short FL2VA clip from one of our existing stills, at strength
  1.0 vs ~0.6, trigger on vs off.
