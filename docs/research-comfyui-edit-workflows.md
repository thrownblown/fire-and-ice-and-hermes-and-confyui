# ComfyUI Image-Edit Workflows — r/comfyui survey

Survey of how people actually wire image-edit models into ComfyUI, gathered from
r/comfyui threads (October 2026). Purpose: feed the wardrobe/prop-swap edit pipeline
for the FNI remake. Every concrete claim carries a source link or an explicit
`unverified` tag.

---

## Executive summary

The community has converged on **two dominant edit-model families** — Qwen Image Edit
and Flux "position-aware" models (Flux.1 Kontext, then Flux.2 Klein) — plus a long tail
of prompt-driven editors (OmniGen, Nano Banana / Gemini). Editing is rarely done as
masked img2img anymore; the modern pattern is **"reference image(s) + natural-language
edit instruction" through an edit-native checkpoint**, with inpainting kept as a
finishing pass for localized fixes. The single biggest practical lever people keep
rediscovering is **quantization choice (FP8 vs GGUF)**: FP8 is materially higher quality
and is the default recommendation whenever the ~22 GB footprint fits, while GGUF (Q4–Q8)
is the low-VRAM fallback. The recurring beginner trap is **distilled/turbo/lightning
LoRAs**, which "plastic-skin" edited faces — widely recommended against for edit models.

---

## Workflow patterns

### Pattern 1 — Reference image + edit instruction through an edit-native checkpoint

The dominant pattern for the last two model generations. A single (or 2–3) reference
image is encoded by the model's vision encoder, and the *whole instruction is the text
prompt* ("make the man in Picture 1 wear the top hat from Picture 2"). No mask required
for coarse edits.

- Models: Qwen Image Edit (2509 / 2511 / 2.1), Flux.1 Kontext, Flux.2 Klein.
- Key detail for Qwen: multi-image prompts **must** be declared as
  `Picture 1: <desc>. Picture 2: <desc>.` — the model was trained on exactly this
  format and misattributes inputs otherwise.
  ([thread](https://www.reddit.com/r/comfyui/comments/1tqm4pb/cracked_the_case_on_high_res_quality_qwen_edit/))
- Flux Kontext ships **day-0 native templates** in ComfyUI (Workflow → Browse Templates
  → Flux Kontext), no custom nodes needed.
  ([thread](https://www.reddit.com/r/comfyui/comments/1ll3emk/flux1_kontext_dev_day0_native_support_in_comfyui/))
- Community verdict: Qwedit is best at **character likeness** (new shots of a character
  from one ref, no LoRA); Klein 9B is better/faster at many general edits but weaker on
  likeness and camera-angle changes.
  ([thread](https://www.reddit.com/r/comfyui/comments/1tqm4pb/cracked_the_case_on_high_res_quality_qwen_edit/))

### Pattern 2 — Masked inpainting / CropAndStitch as localized finishing pass

For swapping a specific region (a garment, a face) people mask the area and run
inpainting, usually at low denoise with a self-referencing reference latent. The
`Inpaint CropAndStitch` node is the standard for splitting large images so the masked
region is processed at full latent resolution.

- (`comfyui-inpaint-cropandstitch` appears repeatedly as the go-to node.
  [thread](https://www.reddit.com/r/comfyui/comments/1rkfwpn/nsfw_image_edite_like_nano_banana_on_3060_12gb/))
- Recurring failure: inpainting leaves a visible **mask outline**; users upscale after
  to blend it away.
- For a compositional merge ("paste object A into scene B") the recommended chain is:
  merge → rewrite the prompt to include the item → low-denoise img2img → optional IC-Light
  relight → masked cut/paste with another low-denoise pass.
  ([thread](https://www.reddit.com/r/comfyui/comments/1gis9xz/any_workflow_that_could_achieve_something_like/))

### Pattern 3 — ControlNet-assisted structural edits

For pose/structure transfer (not identity) people drive edits with ControlNet maps
(Depth, DWPose, Canny, Lineart) instead of, or alongside, a reference image. InstantX
Union ControlNet covers the Qwen family; FLUX.2 uses the Union Pro/2602 via
JLC-ControlNet Orchestrator.

- Reference image (semantics) + ControlNet (structure) + prompt (style) are treated as
  *three competing influence streams*, tuned independently.
  ([thread](https://www.reddit.com/r/comfyui/comments/1vfr9js/a_flux2_controlnet_workflow_to_explore_how/))
- Documented limitation: **ReferenceLatent + ControlNet is not yet supported** on Qwen —
  combining them raises a tensor-shape mismatch, so users pick one conditioning path.
  ([thread](https://www.reddit.com/r/comfyui/comments/1n5w5lw/qwen_referencelatent_controlnet_or_model_patch/))

### Pattern 4 — GGUF quantized loading for low VRAM

The universal low-VRAM pattern: swap the full-precision `LoadDiffusionModel` for
`UnetLoaderGGUF` and pick Q2–Q8. This is how people run Klein 9B and Qwen Edit on 6–12 GB
cards, and the Q2/Q3 quants get Klein down to 2–4 GB cards.

- Recommended CLIP/encoder also goes to CPU or a GGUF/FP8 encoder to free VRAM.
  ([thread](https://www.reddit.com/r/comfyui/comments/1rdkqle/i_created_simple_flux2_klein_9b_gguf_low_vram/),
   [thread](https://www.reddit.com/r/comfyui/comments/1vfdrf3/need_help_setting_up_my_first_workflow_for_qwen/))
- `ComfyUI-GGUF` is the required node pack.

### Pattern 5 — "Double ref" / high-res reference conditioning (the sharpness fix)

The most-cited quality discovery for Qwen Edit 2511: the default Comfy Qwen pipeline
downscales the reference region, which is the root cause of soft/blurry edits. Feeding
the reference image **twice** and controlling input scale/output size explicitly fixes
it — using 100% native Comfy nodes, no custom packs required.
([thread](https://www.reddit.com/r/comfyui/comments/1tqm4pb/cracked_the_case_on_high_res_quality_qwen_edit/))

---

## Model → node pack → VRAM → quality notes

| Model / checkpoint | Node packs (custom) | VRAM / footprint | Quality & speed notes |
|---|---|---|---|
| **Qwen Image Edit 2511 (FP8)** | LayerStyle (scale), SeedVR2 (opt. upscale); native otherwise | FP8 = 22 GB; ~26 GB combined RAM+VRAM; runs on <24 GB via block-swap (slower) | Highest quality for character likeness; "much higher quality than Q8 GGUF"; 20 steps typical (30 = sharper); double-ref mode +50% time but always better for single-image |
| **Qwen Image Edit 2511 (GGUF)** | ComfyUI-GGUF | Q4–Q8 fits 8–12 GB | Only for quants < Q8; Q6 & below noticeably degrade. Lightning/turbo LoRAs → plastic skin, avoid |
| **Flux.1 Kontext [dev]** | None (native template); ComfyUI-GGUF for the GGUF build; Nunchaku for SVDQuant int4 | dev ~ full; INT4 GGUF ≈ 6 GB claimed for the "Ultimate WF"; Nunchaku int4 runs 30 s gens on 8 GB | Easy, day-0 native. Better than OmniGen at keeping faces/clothes; strong at add/remove/relight |
| **Flux.2 Klein 4B / 9B (GGUF)** | ComfyUI-GGUF (+ Flux2 CLIP/VAE loaders) | 9B Q8/Q4 for 8 GB; 4B Q2/Q3 for 2–4 GB cards | Recommended as "more compact, faster, more recent" than Qwen Edit; the `in_b_enhancer` LoRA fixes flat/plastic skin. Weakest at character likeness |
| **Nano Banana (Gemini 2.5 Flash Image, GGUF)** | ComfyUI-GGUF; IF_AI_tools (IF Gemini node) for Krita | GGUF similar footprint to Qwen Edit | API-hosted or local GGUF; strong NSFW-capable edit; good inpainting/instruction |
| **OmniGen / OmniGen2** | ComfyUI_OmniGen_Nodes (set-soft); no native support | heavier, no GGUF path commonly cited | Uncensored; good at add/remove/multi-image composition; "much harder to set up"; prompt phrasing-sensitive (`\|image_#\|` placeholders) |
| **FLUX.2 ControlNet Union** | comfyui_controlnet_aux, JLC-ControlNet Orchestrator | full FLUX.2-dev | Structure/pose edits only; pairs with reference image for semantics |
| **SD1.5 / SDXL inpainting (baseline)** | ComfyUI-Inpaint-CropAndStitch | runs on 12 GB (3060), even 8 GB | Legacy fallback for clothing swaps; mask-outline artifacts, needs upscale; sensible beginner floor but modern edit models supersede it |

Named custom node packs across these workflows: **ComfyUI-GGUF**,
**ComfyUI-Inpaint-CropAndStitch**, **ComfyUI_LayerStyle**, **ComfyUI-SeedVR2**,
**comfyui_controlnet_aux**, **comfyui-kjnodes**, **rgthree-comfy**, **was-node-suite**,
**ComfyUI Inspire Pack**, **Pixorama** nodes, **IF_AI_tools**, **ComfyUI_OmniGen_Nodes**.

---

## Lowest-VRAM viable setup

The floor people report actually working on edit tasks:

1. **4–6 GB cards**: Flux.2 Klein **4B at Q2/Q3 GGUF** (CivitAI "low VRAM" workflows by
   sarcastic-tofu explicitly target 6 GB, with 2–4 GB possible on the previous workflow
   + Q2/Q3).
   ([thread](https://www.reddit.com/r/comfyui/comments/1rdkqle/i_created_simple_flux2_klein_9b_gguf_low_vram/))
2. **8 GB cards**: Flux.1 Kontext via **Nunchaku SVDQuant INT4** — claimed ~30 s per
   generation.
   ([thread](https://www.reddit.com/r/comfyui/comments/1ms8t97/everythings_just_perfect_and_then_theres_one/))
3. **12 GB cards (e.g. 3060)**: Klein 4B/9B GGUF Q4, or Qwen Edit GGUF Q3–Q4; SD1.5/SDXL
    inpainting as a last resort.

The recurring rule-of-thumb below 24 GB: put the **text encoder on CPU** (or use the FP8
encoder) and use the lowest quantization that holds acceptable quality.

---

## Recurring failure modes (community complaints)

1. **Plastic / deep-fried skin** from Lightning/Turbo/distilled LoRAs on edit models —
   the most-often repeated warning across Qwen Edit and Klein threads.
2. **Prompt-only change → 10 s becomes 20 min**: a text change forces full re-encode of
   the Qwen VL text encoder and cache reset; keep VRAM ≤ 90–95%, move encoder to CPU, or
   use FP8 encoder.
   ([thread](https://www.reddit.com/r/comfyui/comments/1o6e1qa/comfyui_qwen_edit_sometimes_jumps_from_10s_to_20/))
3. **ReferenceLatent + ControlNet unsupported** on Qwen (tensor-shape error) — pick one
   conditioning path.
4. **Mask outline / halo** artifact after inpainting or face-swap — needs upscale or
   color-match pass.
5. **Q8-and-below GGUF visibly worse than FP8** for face detail — use FP8 when it fits.
6. **Multi-image Qwen edits misattribute inputs** unless prompted with the
   `Picture 1: / Picture 2:` prefix.
7. **Negative prompts ignored** at CFG ≤ 1.0 (Qwen Edit / Klein / Flux Kontext) — put
   everything in the positive prompt and leave the negative node blank.

---

## Sources (r/comfyui threads)

- Qwen Image Edit 2511 max-quality / high-res deep-dive:
  https://www.reddit.com/r/comfyui/comments/1tqm4pb/cracked_the_case_on_high_res_quality_qwen_edit/
- Qwen Image Edit 2511 4-step "fast editing" workflow:
  https://www.reddit.com/r/comfyui/comments/1pzgyzm/comfyui_workflow_qwen_image_edit_2511_fast_4step/
- Qwen Image Edit 2511 product-compositing (18 h config write-up):
  https://www.reddit.com/r/comfyui/comments/1q8ohx7/experimenting_with_qwen_image_edit_2511_for/
- Qwen Image Edit 2511 "doesn't remove anything" + JSON workflow:
  https://www.reddit.com/r/comfyui/comments/1pul8b3/qwen_image_edit_2511_doesnt_remove_anything/
- Qwen Edit 2509 experimental face-swap workflow:
  https://www.reddit.com/r/comfyui/comments/1o1dr94/qwen_edit_2509_experimental_face_swap_workflow/
- 4-step Qwen-Edit vs Nano Banana vs Kontext (5 use-cases):
  https://www.reddit.com/r/comfyui/comments/1muktkh/4step_fast_qwenimage_edit_workflow_steals_the/
- Flux.1 Kontext [dev] day-0 native support:
  https://www.reddit.com/r/comfyui/comments/1ll3emk/flux1_kontext_dev_day0_native_support_in_comfyui/
- Flux Kontext single-image edit workflow (LLM Toolkit prompt expansion):
  https://www.reddit.com/r/comfyui/comments/1ln49ji/easy_image_editing_with_flux_kontext_locally/
- Flux Kontext "Ultimate" workflow — LoRA/IPAdapter/detailers/upscale:
  https://www.reddit.com/r/comfyui/comments/1lxn52f/a_flux_kontext_workflow_lora_ipadapter_detailers/
- Flux Kontext Ultimate — 8 steps @ 6 GB VRAM (-ish, TEACACHE + LoRA):
  https://www.reddit.com/r/comfyui/comments/1ls5dop/flux_kontext_ultimate_workflow_include_fine_tune/
- Flux Modular WF v6.0 with Kontext (GGUF + standard editions):
  https://www.reddit.com/r/comfyui/comments/1m4kxdl/flux_modular_wf_v60_is_out_now_with_flux_kontext/
- Flux.2 Klein 4B GGUF combined txt2img + edit workflow:
  https://www.reddit.com/r/comfyui/comments/1qesnun/flux_2_klein_4b_gguf_workflow_that_combines/
- Flux.2 Klein 9B all-in-one walkthrough (122 nodes, edit/inpaint/refine):
  https://www.reddit.com/r/comfyui/comments/1so8383/guide_complete_walkthrough_for_every_pipeline_in/
- Flux.2 Klein 9B GGUF low-VRAM workflows (txt2img / inpaint+outpaint / headswap):
  https://www.reddit.com/r/comfyui/comments/1rdkqle/i_created_simple_flux2_klein_9b_gguf_low_vram/
- "Flux Klein instead of Qwen Edit" — first-workflow setup guide:
  https://www.reddit.com/r/comfyui/comments/1vfdrf3/need_help_setting_up_my_first_workflow_for_qwen/
- OmniGen Image Editor (prompt-driven, multi-image):
  https://www.reddit.com/r/comfyui/comments/1h1w0ze/omnigen_image_editor/
- Flux Kontext vs OmniGen2 impressions:
  https://www.reddit.com/r/comfyui/comments/1llbgzp/flux_kontext_dev_vs_omnigen2_your_impression_so/
- OmniGen install/troubleshooting + set-soft ComfyUI nodes:
  https://www.reddit.com/r/comfyui/comments/1kinss3/omnigen/
- Basic OmniGen workflow (placeholder syntax, CPU fallback):
  https://www.reddit.com/r/comfyui/comments/1ghogwb/basic_workflow_for_omnigen/
- "Photoshopped merge, not superimposed" (img2img + low denoise + IC-Light advice):
  https://www.reddit.com/r/comfyui/comments/1gis9xz/any_workflow_that_could_achieve_something_like/
- FLUX.2 ControlNet workflow (prompt vs reference vs ControlNet interplay):
  https://www.reddit.com/r/comfyui/comments/1vfr9js/a_flux2_controlnet_workflow_to_explore_how/
- Qwen ReferenceLatent + ControlNet unsupported:
  https://www.reddit.com/r/comfyui/comments/1n5w5lw/qwen_referencelatent_controlnet_or_model_patch/
- Subgraph mega-workflow (Qwen/Chroma toggles, inpainting, ControlNet):
  https://www.reddit.com/r/comfyui/comments/1nhfqga/using_subgraphs_to_create_a_workflow_which/
- Consistent character from single image (Klein KV / Qwen Edit):
  https://www.reddit.com/r/comfyui/comments/1ryhz6s/is_there_a_way_to_generate_a_consistent_character/
- Nano Banana / Gemini 2.5 Flash Image inpainting:
  https://www.reddit.com/r/comfyui/comments/1qnbjdo/can_i_do_inpainting_with_the_nano_banana_model/
- Nano Banana in Krita (IF Gemini node):
  https://www.reddit.com/r/comfyui/comments/1n3a1u4/nano_banana_in_krita/
- "Edit like Nano Banana on 3060 12 GB" (Klein / SDXL inpainting advice):
  https://www.reddit.com/r/comfyui/comments/1rkfwpn/nsfw_image_edite_like_nano_banana_on_3060_12gb/
- Hyper FLUX + inpainting + upscaler low-VRAM:
  https://www.reddit.com/r/comfyui/comments/1f7mx2w/hyper_flux_inpainting_upscaler_for_low_vram/
- Qwen Edit 10 s → 20 min prompt-change slowdown (root cause analysis):
  https://www.reddit.com/r/comfyui/comments/1o6e1qa/comfyui_qwen_edit_sometimes_jumps_from_10s_to_20/