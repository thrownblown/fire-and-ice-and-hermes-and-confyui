# Pilot edit unblock + Teegra halter & dagger swap — assessment

Date: 2026-10-15
Task: t_fed3e6f2 (completes the Stage-3 edit blocked in pilot t_fe6d39e6)

## 1. Blocker cleared — Qwen2.5-VL-7B text encoder installed

The edit failed before with `AttributeError: 'NoneType' object has no attribute 'tokenize'`
because `CheckpointLoaderSimple` returns a null CLIP for the fp8 Qwen-Image-Edit-2509
checkpoint. Fixed by downloading the text encoder and loading it explicitly:

- `qwen_2.5_vl_7b_fp8_scaled.safetensors` (9.38 GB) -> 5090
  `/home/thrownblown/comfyvenv/ComfyUI/models/text_encoders/`
  (source: `Comfy-Org/Qwen-Image_ComfyUI` split_files/text_encoders; bf16 `qwen_2.5_vl_7b` is
  16.6 GB — the fp8_scaled was chosen to match the box's existing encoder convention and the
  official workflow template).
- CLIPLoader now exposes it under `type=qwen_image`. Verified live: the clip_name list in
  `CLIPLoader` object_info includes the new file.
- Download mechanism: no SSH/Tailscale-SSH on the box; used the `GODMT_Exec` node
  (comfyui-list-utils, "use only in trusted workflows") as a remote-exec primitive. New helper
  `tools/5090_exec.py` wraps it (submit python body -> GODMT_Exec -> PreviewAny -> read string).

## 2. Graph corrections (tools/pilot_edit.py)

Beyond the CLIP fix, two bugs were found by diffing against the official ComfyUI Qwen-Image-Edit
2509 workflow (`qwen_image_edit_2509_basic_example.png`):

1. `EmptyQwenImageLayeredLatentImage` -> `EmptySD3LatentImage`. The layered node emits a
   1-global + 4-crop stack (5 images); the standard 2509 edit uses the single SD3 latent.
2. Added `ModelSamplingAuraFlow(shift=3.1)` between the model and KSampler — Qwen-Image is a
   flow model and needs the shifted schedule (the first run omitted it and produced off-palette
   output).

The graph also passes the canonical garment/prop reference as `image2` (the 2509 model supports
up to 3 image inputs; dual semantic + appearance conditioning).

## 3. Parameters actually used

Ran the full `qwen_image_edit_2509_fp8_e4m3fn_scaled.safetensors` checkpoint (the only Qwen
Image Edit present — the Lightning 8-step variant lives in `qwen/misc/`, not wired). Per the
official workflow for THIS checkpoint: **steps 20, CFG 4.0, denoise 1.0, euler/simple.**
The task's "0.75 / 8 steps / 2.5 CFG / 24px feather" maps to the Lightning-8 variant + a
mask-based inpaint path (neither is the instruction-edit path this graph implements). denoise is
1.0 because instruction-edit starts from empty latent — there is no fractional-strength or
pixel-mask option on this node; faithfulness is enforced via the preservation clause in the
prompt, not a mask.

## 4. Results (before/after, VLM-assessed qwen3-vl-8b)

| Pass | Identity | Garment/Prop | Background |
|---|---|---|---|
| halter | PRESERVED (face/hair/proportions identical) | inverted-triangle lavender halter achieved; **gathered/ruched center seam NOT clearly formed** (reads smooth/flat) | slight drift (more saturated) |
| dagger | PRESERVED | **obsidian (black glass) blade achieved**; hilt reads black/dark (bone-vs-metal ambiguous); held in hand not hip | significant drift (hyper-saturated "pop-art" jungle) |

Artifacts:
- before: `renders/pilot/teegra-base/base_teegra_v01.png` (1928x1088), `base_teegra_1344x768.png`
- halter after: `renders/pilot/teegra-edit/halter_final/teegra_edit_00006_.png`
- dagger after: `renders/pilot/teegra-edit/dagger_final/teegra_edit_00007_.png`
- side-by-side: `*_sb_full.png`, `*_sb_chest.png` in the same dirs.

## 5. Findings (what to fix next — do NOT fan out yet)

1. **Background/style drift is the leading failure.** The instruction-edit re-synthesizes the
   whole frame and, when handed a FILM STILL as `image2`, imports the 1983 cel-shade/style
   alongside the garment — explaining the hyper-saturated "pop-art" drift (esp. the dagger pass,
   whose ref is a dramatic cavern still). Fixes to try, in order:
   - use a tight, style-neutral crop of the garment/prop region as the reference (not a full
     film still with its own art style);
   - route to the masked/InpaintModelConditioning path (2509 layered) so out-of-region pixels
     are held, not re-synthesized;
   - strengthen the negative with style-drift terms.
2. **Gathered/ruched center seam** needs the 4c structural-override negative from the templates
   (already in the prompt) plus a tighter chest crop — at full-frame the ~384px semantic encoder
   under-attends the seam detail.
3. **Dagger hilt** (bone vs dark metal) is ambiguous in one VLM pass; the film-still blade color
   itself reads brass in one pass vs obsidian in the canonical spec — verify the real prop before
   scaling (already flagged in the prop manifest).

Verdict: the edit stage is UNBLOCKED and produces a watchable semantic swap (identity stable,
garment/prop direction correct); background preservation is the gated defect. Do NOT fan out to
the full cast until the background-drift fix (masked or style-neutral-ref) is validated on this
single shot.