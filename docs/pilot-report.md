# Pilot report — one character through the Krea→edit pipeline

Date: 2026-10-15
Worker: default (task t_fe6d39e6)
Pipeline spec: docs/plans/2026-10-15-krea-to-edit-shot-pipeline.md
Templates: docs/edit-swap-templates.md · Asset schema: docs/asset-schema.md

## TL;DR

Stage 1 (generate) and Stage 2 (select) run end-to-end on the 5090 and produce a clean,
coherent 1980s-fantasy base still. Stage 3 (edit) is blocked by ONE missing model file: the
Qwen-Image-Edit-2509 text encoder (Qwen2.5-VL-7B) is not installed, so the edit graph dies at
the text-encode step. Everything else (edit node, checkpoint, VAE) is present.

Recommendation: CONDITIONAL GO — scale generate→select→asset-packing now; install the one
missing text encoder and complete a single edit pass before scaling the edit half.

---

## 1. Character and canonical assets chosen

Character: Teegra (the documented pilot subject — the wardrobe-drift motivating case).
- Garment: teegra.top.halter — lavender inverted-triangle gathered-center halter
  (geometry specified in docs/qwen_edit_teegra_prompts.md).
- Prop: melee.obsidian_dagger — black obsidian blade, carried at the hip.

Canonical reference source: real film stills at refs/characters/TEEGRA/ (30+ images).
Note: these stills are NOT yet ingested into the asset-library structure; the only character
in the asset library (aria) has 32x32 colour placeholders as refs — see failure mode 3.

## 2. Stage 1 — Generate (Krea 2, 5090)

Driver: tools/pilot_generate.py (clean rebuild of tools/krea2_stills.py).
Workflow graph: probes/krea2_5090_template.json (saved Krea2 graph, node IDs 135/137/124/102/128).

Exact prompt used:
- MAIN: "A 1980s dark fantasy heroine in the style of Frank Frazetta and Ralph Bakshi
  animation. Long flowing jet-black hair parted down the middle, fair skin, winged eyeliner,
  muted red lips. She wears a loose lavender cloth halter top and carries a black obsidian
  dagger at her hip. Full-body heroic barbarian princess standing in a misty swamp clearing,
  cel-shaded vintage animation colors, flat yet rich."
- PRE: "retr0fantasy, 60s Soviet fantasy-film, subtle film grain, aged theatrical print
  quality, caucasian"

Parameters: seed 424242, sampler er_sde/sgm_uniform, steps 9, cfg 1.0, 16:9 @ 2.0 MP.
LoRAs: retro-fantasy (lora_7) ON @ 1.0; lora_1 (a celebrity-likeness LoRA) OFF; lora_10 (a second
celebrity-likeness LoRA) OFF. (The saved graph ships with those two celebrity-likeness LoRAs live — see
failure mode 2.)

Artifact: renders/pilot/teegra-base/base_teegra_v01.png (1928x1088).

## 3. Stage 2 — Select (self-assessment, no human available headless)

VLM description (qwen3-vl-8b via tools/vlm_describe.py) of the base:
- Identity: long black hair, fair skin, intense eyes, bold red lips — reads canonical.
- Garment: "halter top of sheer flowing purple fabric, deep V-neckline, tied at the sides" —
  a halter but NOT the canonical inverted-triangle gathered-center halter. This is the
  intended edit target (Krea drifted the top, exactly as the spec predicts).
- Prop: "short dagger, black hilt with ornate design" — roughly right, not canonical.
- Background/lighting: misty jungle, soft diffused light, Frazetta/Bakshi pulp style — good.

Verdict: composition/pose/lighting/likeness PASS (Stage-1 gate). Wardrobe/prop deliberately
NOT judged here. Base accepted as approved_base for the edit.

## 4. Stage 3 — Edit (Qwen-Image-Edit-2509, 5090) — BLOCKED

Driver: tools/pilot_edit.py. Native ComfyUI Qwen-Image-Edit graph:
CheckpointLoaderSimple(qwen_image_edit_2509_fp8_e4m3fn_scaled.safetensors) → M/C/V;
LoadImage(base) → TextEncodeQwenImageEditPlus(clip, prompt, vae, image1) → positive;
TextEncodeQwenImageEditPlus(clip, prompt=negative) → negative;
EmptyQwenImageLayeredLatentImage(1344x768, layers=1); KSampler(20 steps, cfg 2.5, euler/simple,
denoise 1.0); VAEDecode; SaveImage.

Result: the graph queues, checkpoint + VAE + empty-latent execute, then the negative
text-encode node fails:

    execution_error node_id=4 node_type=TextEncodeQwenImageEditPlus
    AttributeError: 'NoneType' object has no attribute 'tokenize'
    clip.tokenize(...)  -> clip resolved to null

Root cause (verified against the 5090 object_info): the CLIP input is null because
CheckpointLoaderSimple returns a null CLIP for this checkpoint — qwen_image_edit_2509_fp8_...
is a diffusion-only (fp8) checkpoint. Qwen-Image-Edit-2509 needs its Qwen2.5-VL-7B text
encoder loaded separately via CLIPLoader(type=qwen_image), and that encoder is NOT in the
clip directory. Full clip list (22 files) contains Qwen3-VL / gemma / t5 / umt5 — no
Qwen2.5-VL-7B.

Present vs missing (authoritative, read live from the 5090):
- Qwen-Image-Edit-2509 checkpoint (fp8): PRESENT (CheckpointLoaderSimple ckpt_name).
- Qwen Image VAE (qwen_image_vae.safetensors): PRESENT.
- TextEncodeQwenImageEdit / Plus nodes: PRESENT (comfy_extras.nodes_qwen).
- Qwen2.5-VL-7B text encoder (clip type qwen_image): MISSING → the blocker.

## 5. Top 3 failure modes and fixes

1. Edit text encoder missing. The Qwen-Image-Edit-2509 model is installed but its
   Qwen2.5-VL-7B text encoder is not, so every edit pass fails at text-encode with a null
   CLIP. Fix: download the Qwen2.5-VL-7B-Instruct text encoder in ComfyUI qwen_image format
   to the 5090 clip directory, then wire it via CLIPLoader(type=qwen_image) instead of taking
   CLIP from CheckpointLoaderSimple. One file (~15 GB), then the whole edit path is testable.

2. The saved Krea2 workflow is not production-clean. probes/krea2_5090_template.json ships
   with an explicit adult prompt baked into the main text field and two live character LoRAs
   (lora_1, a celebrity-likeness LoRA, @ 0.7; lora_10, a second, @ 0.7). Any reuse that only swaps the
   prompt text still leaves those LoRAs active. Fix: publish a scrubbed "house" Krea2 template
   with lora_1/lora_10 defaulted off and a neutral main prompt; keep only the retro-fantasy
   house LoRA live. (pilot_generate.py already enforces this, but it should be the default.)

3. Canonical asset references are placeholders, not garments. The asset library's only
   character (aria) points at 32x32 colour swatches, and the real Teegra film stills live
   outside the library at refs/characters/TEEGRA/ un-ingested. Handing a 32x32 block as the
   edit's vision reference cannot drive a real garment swap. Fix: ingest the real Teegra stills
   (face.front / body.front / top.halter front / dagger front) into
   assets/characters/teegra/… with manifest status=approved, then let tools/asset_lookup.py
   pack them. This is the single highest-leverage data task before any real edit pass.

## 6. Side-by-side consistency assessment

Only the pre-edit baseline is assessable (the edit is blocked). Before state, from the VLM:
identity = canonical (black hair / fair skin / red lips); garment = WRONG (plain deep-V halter
vs inverted-triangle gathered halter); prop = approximate (ornate black-hilt dagger, non-canonical
blade); background/lighting = good (misty jungle, soft top light). The garment is precisely the
drift the edit stage exists to correct, so the test vector is valid; the after/garment-accurate
side is pending the text-encoder fix.

## 7. Go / no-go

- Generate → Select → Asset-pack: GO. Proven end-to-end on the 5090 with clean artifacts.
- Edit (Qwen / Klein): CONDITIONAL. Infrastructure is ~90% present (edit nodes + checkpoint +
  VAE all live; only the Qwen2.5-VL-7B text encoder is missing). After that single download,
  the Qwen-Edit garment/prop swap is directly testable. Klein (Flux2Klein) nodes are present as
  auto-download stubs but the model is not confirmed downloaded — keep it gated per the spec.

Scaling verdict: do not fan out edit passes to the full cast yet. Complete ONE real
garment-swap (Teegra halter) end-to-end after installing the text encoder + ingesting real
reference stills; use that single shot to validate identity-preservation and re-synthesis
drift before committing to the whole cast.

## 8. Artifacts (absolute paths)

- renders/pilot/teegra-base/base_teegra_v01.png            (1928x1088 base)
- renders/pilot/teegra-base/base_teegra_1344x768.png       (resized edit input)
- renders/pilot/aria_pack.json                             (asset-lookup pack, lookup stage proof)
- tools/pilot_generate.py · tools/pilot_edit.py · tools/vlm_describe.py  (pipeline drivers)
- (edit output: none — blocked, see §4)
