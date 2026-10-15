# MiniMax H3 Character-Swap LoRA + 3-way character-sheet workflow (Akatz Labs + Ep39)

Files dropped by Alex 2026-10-15:
- `h3_character_swap_pro4500_1000.safetensors` — the character-swap LoRA (155 MB)
- `MINIMAXA CHARACTER SWAP patreon (1).json` — its Ref2VA workflow
- `Ep39 Character Sheets_Krea vs Qwen 2.1 vs Minimax H3.json` — the 3-way sheet workflow

## 1. Character Swap LoRA (`h3_character_swap_pro4500_1000.safetensors`)

Verified from the safetensors header:
- Base model: `minimax_h3_ref2va` (`ss_base_model_version`) — a **REF2VA** DiT LoRA, not FL2VA.
- 416 tensors, paired `lora_A`/`lora_B` on `attn.{qkv,out}_proj` + `mlp.{fc1,fc2}` —
  a standard character-targeting DiT LoRA (same shape family as retro-fantasy).
- Trained with `ostris/ai-toolkit` 0.13.21; checkpoint at step 1000 / epoch 6.
- Author: Akatz Labs. HF: `akatz-ai/MiniMax-H3-Character-Swap-LoRA`.

**What it does (the headline):** swap a foreground character in a *source video* for a
*reference character* in `<Picture 1>`, carrying identity/outfit/art style from the
picture while preserving the video's camera, framing, background, lighting, objects,
and all *other* people and matching the replaced figure's position/scale/pose/movement.
No trigger word required.

### The workflow it runs in (`MINIMAXA CHARACTER SWAP patreon (1).json`)

- UNet: `minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot.safetensors`
- CLIP: `qwen3vl-32B-MiniMax-H3-Q2_K.gguf` (GGUF loader, type `minimax`)
- VAE: `minimax_h3_video_vae_int8_convrot.safetensors`
- LoRA: `h3_character_swap_pro4500_1000.safetensors` @ strength 1.0 (LoraLoaderModelOnly)
- Sampler: res_multistep / simple, 8 steps, 24 fps, 17n+5 frames (5s → 124 frames)
- Resolution: 0.4 MP / 864×480 start; 0.98 MP / 1344×768 for 768p
- Reference prep: the `<Picture 1>` image is background-stripped via **RMBG-2.0** before
  feeding `ref_image_0`, then resized. Source clip via `VHS_LoadVideo` (force_rate 24,
  no fps resample — convert non-24-fps clips beforehand).

The core swap prompt (the exact contract the model was trained to):
```
Replace only the woman in the foreground in <Video 1> with the character in <Picture 1>.
Keep the replacement character's identity, outfit, and art style from <Picture 1>.
Preserve the source video's camera, framing, background, lighting, objects, and all other people.
Match the selected woman's position, scale, pose, and movement throughout the clip.
Do not show the reference sheet or its background.
```

Note the workflow ships a `ref_image_size: match` on the ReferenceToVideo node — the
opposite of FNI's standing `max` rule. Marked as an open tension (see below).

## 2. The 3-way character-sheet workflow (Ep39)

The free workflow backing the comparison video. Three parallel branches, one per engine:

| engine | UNet | CLIP | LoRA |
|---|---|---|---|
| Krea 2 | `krea2_turbo_int8_convrot` | `qwen3vl_4b_int8_convrot_learned` (krea2) | `krea2_identity_edit_v1_2` @ 0.9 |
| Qwen 2.1 | (Krea2EditGroundedEncode path) | — | `Qwen2_1/CharSheet.safetensors` @ 1.0 |
| MiniMax H3 | `Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8` via `SatoDiveH3Image` | `qwen3vl_32b_minimax_h3_int8_convrot` | — |

Notable: the H3 branch uses **Sato Dive's `SatoDiveH3Image`** node (the workflow the
comparison video credited). Also references **Pixaroma** (PixaromaMonitor/RunTimer nodes)
— the LoRA the author said "you really should download."

## 3. Why this matters for FNI — a third identity route

FNI's identity problem has had two answers so far: (A) Krea generate → Qwen-Edit
wardrobe swap (the kanban pipeline), and (B) H3 ref2va holding a character sheet. This
drop adds (C): **character swap** — take a source clip whose *motion/camera/pose* is
right but whose *person* is wrong, and transplant the canonical character in.

For the 80s-pivot in particular this is the strongest match yet to the "replace the
rotoscope figure with live-action Teegra" idea: the 1983 source clip supplies the
choreography/framing, the reference sheet supplies live-action Teegra identity, and the
swap LoRA does the transplant — instead of fighting H3 to restyle rotoscope cells while
REF2VA holds them.

## Open items / caveats

1. **`ref_image_size: match` vs our `max` rule.** The swap workflow ships `match`; the
   skill's identity-anchor rule says `max` (never `match` — it blends two faces). For a
   swap whose whole point is matching scale/pose to the *video*, `match` may be
   deliberate; unresolved until a run is judged.
2. **Files not yet on the 5090** — the LoRA and this workflow are in Downloads. Landing
   the LoRA at `models/loras/` on the 5090 is the next concrete step before any test.
3. **The Ep39 H3 stack differs from ours** (Singularity ref2va + SatoDiveH3Image node) —
   the node is a custom pack not confirmed on the 5090; check before assuming it runs.
4. **Prompt contract is rigid** — the swap LoRA was trained to the exact
   replace/preserve/match wording. Rewriting it in FNI's 6-field grammar would likely
   break the effect; the swap is a separate, prompt-literal code path, not a
   style we fold into refrun.