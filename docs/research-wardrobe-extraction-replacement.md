# Wardrobe Extraction & Clothing Replacement — State of the Art (r/stablediffusion + r/comfyui)

Survey of community-reported techniques for two distinct problems:
1. **Extraction** — isolating / segmenting a garment or outfit from a photo (mask or cutout).
2. **Replacement** — putting a *different* garment onto a person while preserving identity, pose, and framing.

Scope note: "preserving identity and pose" maps directly to the FNI use case (dress the same character in a new wardrobe across shots, without changing their face, body, or camera position). The single most influential community finding for *our* stack is captured in the MiniMax note at the bottom of Part B — read it.

---

## PART A — Extraction (segmentation / cutout of a garment)

The community is unanimous that there is **no single magic model** for "extract just the outfit." The winning pattern is always a two-stage pipeline: (a) a *detector/grounder* that finds the garment and produces a rough box or region, then (b) a *segmenter* that refines it to pixels. Dedicated clothing-parsing models are the exception that does it in one stage, at the cost of fixed categories.

### A1. GroundingDINO + SAM / SAM-HQ  (text-prompt → bounding box → mask)

- **What it needs:** an image + a short text prompt naming the garment ("skirt", "shirt", "jacket"). GroundingDINO detects it and returns a box; SAM (or the higher-detail SAM-HQ variant) converts the box into a pixel mask.
- **ComfyUI:** yes — `comfyui_segment_anything` (storyicon) is the canonical node pack; the same `GroundingDinoSAMSegment` node is used inline in many inpaint workflows. Models auto-download.
- **VRAM:** light. SAM ViT-B runs on a few GB; ViT-H is better quality but heavier.
- **Quality:** regarded as "the best *zero-shot automatic* masking solution" for a few years; won the zero-shot challenge leaderboard. Good on named garments, weak on fine/abstract targets ("nose", "mouth" select the whole face).
- **Failure cases:** only succeeds ~1/3 of the time on clothing specifically (one report), leaving stray arm/hand pixels; needs manual cleanup or mask add/subtract pass. Community trick: segment a *broader* region (upper body) then subtract hands/face rather than targeting the garment directly — hair and skin are detected more reliably than cloth.
- **Readiness:** production-ready for masking; not ready for *clean garment cutouts* without cleanup.
- Sources: [1](https://www.reddit.com/r/StableDiffusion/comments/13old1j/is_there_a_way_to_do_segmentation_of_a_persons/jl57sjj/), [2](https://www.reddit.com/r/comfyui/comments/18wuacc/auto_masking/), [3](https://www.reddit.com/r/StableDiffusion/comments/1agw29w/auto_masking_through_clothing_segmentation/)

### A2. Florence-2 + SAM2  (open-vocabulary grounding → SAM2 mask)

- **What it needs:** image + prompt (or no prompt — Florence-2 can region-caption autonomously). Florence-2 is a stronger, more modern *grounder* that returns phrases + boxes; SAM2 turns the boxes into masks.
- **ComfyUI:** yes — Kijai's `segment-anything-2` pack is the reference; `ComfyUI-Florence2` provides the grounding nodes. Many "mask by prompt" workflows ship as embedded-PNG JSON.
- **VRAM:** moderate — SAM2 is heavier than SAM but still a few GB, not the bottleneck in an edit stack.
- **Quality:** the current default for *semantic* masking (understand the object, not just detect it). Better than GroundingDINO for multi-object / "person + garment" separation, and can isolate one person among several by feeding a "person" box down to a finer box.
- **Failure cases:** still not guaranteed per-image; community consensus (even the "best SAM" threads) is that every auto-segmentation needs a tweak-per-image unless the subject is a clean T-pose. Mask add/subtract (upper body + shirt − hands) is the standard cleanup idiom.
- **Readiness:** production-ready, the recommended extractor of 2025-2026 threads.
- Sources: [4](https://www.reddit.com/r/comfyui/comments/1f86mum/connecting_florence2_captions_to_sam2_masks_can/), [5](https://www.reddit.com/r/comfyui/comments/1odouse/i_built_a_simple_grounding_package_15_models_3/), [6](https://www.reddit.com/r/comfyui/comments/1glmqkp/apart_from_sam2_which_prompt_based_masking_tool/)

### A3. SegFormer B2/B3 clothing parsers (dedicated fashion segmentation)

- **What it needs:** image only — no prompt. These are fine-tuned SegFormer models that directly label garment classes (upper-clothes, pants, dress, coat, etc.).
- **ComfyUI:** yes via `mmdj/segformer_b2_clothes`, `seed99/segformer_b3_fashion`, `seed99/segformer_b3_clothes` on HuggingFace; a node pack (`ComfyUI_LayerStyle`) exposes a **PersonMaskUltra V2** node built specifically for clothing masking, and several SDXL/Flux inpaint workflows ship these models.
- **VRAM:** low.
- **Quality:** the most *reliable per-image* on real photographs because it doesn't depend on a text prompt. The community trick that most improves it: invert selection ("mask everything *except* the garment, then reverse") because the models are better at recognizing skin/hair than differentiating garment classes.
- **Failure cases:** fixed label set — can't target "that fur loincloth" as a concept; fine detail (seams, folds) is not the mask's job, the mask is coarse.
- **Readiness:** production-ready for *masking clothing regions*; not a cutout tool.
- Sources: [3](https://www.reddit.com/r/comfyui/comments/1lpslyr/clothing_segmentation_workflow_help_needed/)

### A4. SCHP / Atlas / LIP / human-parsing (what VTON models use internally)

- **What it needs:** image only; outputs a dense body-part parse map (face / hair / arms / torso / upper / lower / shoes).
- **ComfyUI:** not as a standalone node typically — this is the *preprocessing backbone inside* OOTDiffusion and VITON-HD-style try-on. It exists as standalone repos (Atlas, SCHP).
- **Quality:** the reason try-on pipelines use it — a body-part map is exactly the "where does clothing end and skin begin" signal a try-on model needs. Not for cutouts.
- **Readiness:** production (as a component), experimental (as a user-facing extraction tool).
- Sources: [7](https://github.com/levihsu/ootdiffusion), [8](https://arxiv.org/pdf/2403.01779)

### A5. Ancillary extractors (situational)

- **Clipseg / YOLO / SAM3 / Color-mask:** Clipseg for text-based mask when GroundingDINO misses; YOLO (person/faces) for bounding objects when you want a box not a mask; SAM3 (new, in `ComfyUI-RMBG` v3.0) and the package's Florence-2/YOLOv8 nodes give fast polygon masks. rmbg/BEN2 for background removal → multiply with a person mask to isolate the subject + outfit silhouette.
- Sources: [4](https://www.reddit.com/r/comfyui/comments/1f86mum/connecting_florence2_captions_to_sam2_masks_can/), [5](https://www.reddit.com/r/comfyui/comments/1qg0q52/comfyuirmbg_v300_released_major_update_new/)

**Extraction ranking (production utility):**
1. Florence-2 + SAM2 (open-vocab, multi-subject, current default)
2. SegFormer clothing parser (per-image reliability on real photos, no prompt)
3. GroundingDINO + SAM/SAM-HQ (mature, prompt-based, needs cleanup)
4. SCHP/Atlas human-parsing (only as a VTON preprocessing stage)

---

## PART B — Replacement (clothing swap / virtual try-on)

Two families: **dedicated VTON models** (garment-image in → wearing-pose out) and **mask-inpaint / edit-model pipelines** (mask the clothing region, regenerate it, often conditioned on a garment reference). The edit-model family is what FNI already runs (Qwen-Edit / Klein-Edit on the 4090); VTON is the "true" try-on but is heavier and mostly non-commercial.

### B1. IDM-VTON (yisol) — dedicated VTON, accuracy leader among open models

- **Inputs:** person photo + a standalone garment image (masked garment).
- **ComfyUI:** yes — `ComfyUI-IDM-VTON` (TemryL) and a `pzc163/ComfyUI-IDM-VTON` port; also a Gradio app + HuggingFace Space.
- **VRAM:** ~16 GB recommended; 5 s/image on an RTX 4090; FP8/offload work was in progress to cut this.
- **Identity/pose:** best-in-class for garment↔body alignment among open models, but reports it **alters body proportions** (models get slimmer) and re-inpaints the whole torso.
- **Failure cases:** only supports `upper_body` in the main release (no pants/dresses); fabric detail can come out over-smoothed (community fix: post-process with Flux Fill for texture); **licensing — non-commercial only** (dealbreaker for a shipping film).
- **Readiness:** production-quality output, but *experimental to adopt* here due to non-commercial license + upper-body limitation.
- Sources: [9](https://www.reddit.com/r/StableDiffusion/comments/1ce2iax/idmvton_virtual_tryon_is_just_another_level/), [10](https://www.reddit.com/r/comfyui/comments/1h74itl/best_model_for_virtual_try_on/), [11](https://www.reddit.com/r/sdforall/comments/1ciu79w/idmvton_virtual_try_on_is_simply_mind_blowing_can/)

### B2. Flux.1 Fill + Redux (+ ACE++ / aVTONora / Insert-Anything LoRA) — the community's top *open* recommendation

- **Inputs:** target image with clothing masked; garment reference via Flux Redux (image conditioning) or a text caption; optional ACE++ / aVTONora subject LoRA to bind identity.
- **ComfyUI:** yes — native Flux Fill nodes; several end-to-end "near perfect VTON" workflows are distributed as embedded-PNG JSON. One widely-shared advice: use the IDM-VTON auto-mask as the Flux Fill mask and joycaption the garment as the prompt → "gets you 90%."
- **VRAM:** moderate-high (Flux-class); tolerates 8-16 GB depending on quantization.
- **Identity/pose:** preserves pose/background well (it's inpainting), identity held by the LoRA or by a masked-out face (mask keeps face pixels untouched). **Strongest general-purpose open replacement route.**
- **Failure cases:** seams around the inpaint region (community adds an optional "seams fix" pass); fabric over-smoothing unless you caption the garment and let Redux carry detail.
- **Readiness:** production-ready.
- Sources: [10](https://www.reddit.com/r/comfyui/comments/1h74itl/best_model_for_virtual_try_on/), [12](https://www.reddit.com/r/StableDiffusion/comments/1k06rrx/near_perfect_virtual_try_on_vton/), [13](https://www.reddit.com/r/comfyui/comments/1ka58qq/virtual_try_on_accuracy/)

### B3. CatVTON (pzc163) — lightweight dedicated VTON

- **Inputs:** person + garment image; no separate pose control (unlike IDM-VTON it does not use OpenPose).
- **ComfyUI:** yes — `Comfyui-CatVTON`; a Flux variant of CatVTON exists and reportedly outperforms earlier versions.
- **VRAM:** the lightest of the dedicated VTON models.
- **Identity/pose:** **pose can drift** because it lacks explicit pose conditioning; body proportions can shift too.
- **Failure cases:** output resolution is low (becomes obvious outside a thumbnail); upscale (Topaz/ESRGAN) is a near-mandatory follow-up; detailed fabric texture needs a Flux-Kontext/Flux-Fill cleanup.
- **Readiness:** production-ready *only* as a cheap first-pass + upscale; experimental for hard identity/pose fidelity. Licensing also flagged non-commercial in some threads.
- Sources: [14](https://www.reddit.com/r/StableDiffusion/comments/1er9s8i/how_to_create_model_try_on_photos_like_this/), [10](https://www.reddit.com/r/comfyui/comments/1h74itl/best_model_for_virtual_try_on/), [15](https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/virtual_try_on/)

### B4. OOTDiffusion (levihsu) — academic, full-body capability

- **Inputs:** full-body person photo + garment image + garment category (0=upper, 1=lower, 2=dress).
- **ComfyUI:** not native — runs via Python (`run_ootd.py`); AAAI 2025 paper, "outfitting fusion" (no explicit garment warping, unlike VITON-HD).
- **VRAM:** moderate; needs its own conda env (torch 2.0.1).
- **Identity/pose:** strong conceptually (OpenPose + human-parsing driven), but community reports IDM-VTON and CatVTON produce better practical results; nobody in these threads ranks it #1.
- **Readiness:** experimental-to-usable; the heavyweight academic option when you need *full-body* (lower-body/dress) try-on, which IDM-VTON can't do.
- Sources: [7](https://github.com/levihsu/ootdiffusion), [8](https://arxiv.org/pdf/2403.01779), [16](https://www.reddit.com/r/StableDiffusion/comments/1bhqdro/dress_your_virtual_influencer_comfyui_workflow/)

### B5. Qwen-Image-Edit try-on + "clothing extractor" LoRAs — edit-model route, already in FNI's stack

- **Inputs:** target image + a garment/outfit reference (or just a text prompt). Two community LoRAs specifically: an *Outfit Try-On* LoRA and a *Clothing Extractor* LoRA; the extractor pulls the garment out of image 1, which you then feed as the reference to dress image 2.
- **ComfyUI:** yes — standard Qwen-Edit workflow + the LoRA swapped in.
- **VRAM:** runs on the 4090's ComfyUI (Qwen-Edit FP8/GGUF); slow on low VRAM.
- **Identity/pose:** preserves pose/framing well; **identity caveat — Qwen-Edit output tends toward "plastic/artificial skin"**; the fix community uses is an identity pass (face detailer / FaceID IP-Adapter masked to face) rather than a prompt word.
- **Failure cases:** the "preserve the face" prompt *does not work* — the model re-renders whatever the edit touches, so face stays intact only when it's outside the edited region or masked out. Clothing sometimes inherits the plastic finish.
- **Readiness:** production-ready — this is the family FNI already runs for wardrobe passes.
- Sources: [17](https://www.reddit.com/r/StableDiffusion/comments/1nbzh2d/clothes_try_on_clothing_transfer_qwen_edit_loraa/), [18](https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/klein_or_qwen/), [19](https://www.reddit.com/r/StableDiffusion/comments/1n1n81o/qwenimageedit_prompt_guide_the_complete_playbook/)

### B6. Flux.2 Klein 9B — edit-model with the best natural fabric/identity

- **Inputs:** target image (optionally + a second reference image for the outfit); in-paint conditioning for garment swaps.
- **ComfyUI:** yes (`Flux 2 Klein` nodes + GGUF quants; Klein 4B for low VRAM).
- **VRAM:** 9B needs a real GPU; Klein 4B Q2/Q3 runs on 2-6 GB.
- **Identity/pose:** best-in-class for *realistic* (non-plastic) clothing, better than Qwen-Edit on fabric realism. Weakness: for pose/expression *changes* it reverts to a generic likeness; for clothing changes specifically it holds identity well (clothing edits are the "safe" edit that leaves the face largely untouched).
- **Failure cases:** pixel/identity drift more severe than Qwen-Edit on some inputs — community fix is masked in-paint + "keep everything else consistent" phrasing + paste-by-mask compositing of the unchanged regions.
- **Readiness:** production-ready; FNI's second edit weapon.
- Sources: [18](https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/klein_or_qwen/), [20](https://www.reddit.com/r/StableDiffusion/comments/1tdi287/which_model_is_best_for_image_editing_maintaining/), [21](https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/why_preserve_the_face_prompts_fail_in_edit_models/)

### B7. FitDiT (SDXL-based) — 8 GB VRAM alternative

- **Inputs:** person + garment; runs on ComfyUI.
- **VRAM:** ~8 GB (community-tested).
- **Identity/pose:** quality comparable to IDM-VTON but **inpaints the whole body**, so body size/proportions can change; shares the general VTON body-shape drift.
- **Readiness:** usable fallback for low VRAM; not a top pick on a 4090.
- Sources: [15](https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/virtual_try_on/)

### B8. Closed / hosted (context, not candidates)

- **Fashn** — tops the Alphabake leaderboard for identity + fabric realism; API-only, not local/open. What the community uses to *validate* the concept before chasing open models.
- **Krea 2 Identity Edit** — praised for pose/framing preservation; needs node + LoRA + workflow; runs on Krea's stack.
- **Grok / Nano Banana (Gemini)** — very good reference-image try-on but not practical to self-host.
- **SAL-VTON** — older, superseded (OOTDiffusion reported better).
- Sources: [22](https://www.reddit.com/r/comfyui/comments/1mow8vn/best_virtual_tryon_model/), [23](https://www.reddit.com/r/StableDiffusion/comments/1wb0dt4/need_recommendation_changing_outfits_while/), [16](https://www.reddit.com/r/StableDiffusion/comments/1bhqdro/dress_your_virtual_influencer_comfyui_workflow/)

**Replacement ranking (production utility for FNI):**
1. Flux.1 Fill + Redux (mask-inpaint, open, pose-stable) — best *open* general route
2. Qwen-Image-Edit / Flux.2 Klein 9B (edit-models already in our stack) — best for identity-preserving single-image wardrobe edits
3. IDM-VTON (best raw try-on accuracy, but non-commercial + upper-body only)
4. CatVTON (cheap first pass, needs upscale) / OOTDiffusion (full-body academic) / FitDiT (8 GB fallback)

### MiniMax H3 note (directly relevant to FNI)

A thread on r/stablediffusion tested swapping only clothing in MiniMax video and reported **<50% success**: the outfit reverted to the original after ~5-6 s unless (a) a dedicated reference image of the character *already in the new outfit* was supplied, or (b) the retention-analysis / subject-definition prompt fields explicitly re-stated the new clothing every time. Without a reference image of the character wearing the target garment, H3 falls back to its first subject reference when the scene changes. The practical takeaway for our pipeline: **for H3 video, always generate a "character in desired outfit" reference still first (via the edit-model/VTON routes above), then use that as the subject reference — don't try to swap clothes with prose alone.** [24](https://www.reddit.com/r/StableDiffusion/comments/1wzh4yf/has_anyone_tried_minimax_swap_only_clothes/)

---

## Recommended end-to-end pipeline (step by step)

Target: put a target garment on a FNI character still, preserve face + pose, and produce a clean garment cutout for the wardrobe asset library. Runs on the 4090 ComfyUI (restyle box) and/or the 5090.

1. **Extract the garment cutout** (wardrobe asset library + as the try-on reference).
   - Load the source garment photo → **Florence-2** (region caption) to ground the garment, feed the box to **SAM2** for the pixel mask. (Fallback for plain photos: **SegFormer clothing parser** → PersonMaskUltra V2.)
   - Clean with mask add/subtract (upper body + garment − hands) and a small erode/dilate. Export the cutout as a transparent PNG → this is the asset-schema `wardrobe` image.

2. **Prepare the target image** (the character still to dress).
   - Segment the *currently-worn* clothing region with the same extractor (Florence-2 + SAM2 or SegFormer). Output = the replacement mask. Keep the face, hands, and background explicitly OUT of the mask.

3. **Replace the clothing** (choose by priority).
   - **Primary — Flux.1 Fill + Redux:** inpaint the masked region, conditioning the new garment via Flux Redux (feed the step-1 cutout) or a joycaption of the garment; bind identity with ACE++/aVTONora LoRA or a masked FaceID IP-Adapter. 90%-quality route, pose/background stable.
   - **Secondary — Qwen-Image-Edit / Flux.2 Klein 9B:** feed the target + the step-1 cutout as reference, prompt "replace the clothing with <garment>; keep face, pose, lighting, background unchanged." For Klein, add in-paint conditioning and crop/"paste-by-mask" the unchanged regions. Qwen = faster/pose-stable but watch plastic skin; Klein = better fabric but watch identity drift.

4. **Identity pass** (mandatory after any re-render that touches torso):
   - Face detailer / faceswap node against a neutral headshot of the character, masked to the face. Never rely on "preserve the face" prose — mask it or re-assert it in a separate pass.

5. **Upscale / seam cleanup:** UltimateSDUpscale or ESRGAN/Topaz on the result; Flux-Kontext or a Flux-Fill seams-fix for the inpaint boundary.

6. **For H3 video use:** save this dressed still as the character's reference image for the shot; carry the garment text into subject-definition + retention-analysis fields. Do not rely on the video prompt to hold the wardrobe.

### Quick "what to try first"
For a single still, cheapest ≤30 min: SegFormer mask → **Qwen-Image-Edit** (try-on LoRA) → face detailer. For best open-quality identity+pose fidelity: **Flux.1 Fill + Redux + ACE++** with the SegFormer/SAM2 mask. Reserve IDM-VTON for isolated upper-body garment trials only (license + limb limits).

---

## Sources

1. Is there a way to do segmentation of a person's clothing? — https://www.reddit.com/r/StableDiffusion/comments/13old1j/is_there_a_way_to_do_segmentation_of_a_persons/jl57sjj/
2. auto masking? (HQ-SAM + GroundingDINO) — https://www.reddit.com/r/comfyui/comments/18wuacc/auto_masking/
3. Clothing segmentation — Workflow & Help needed (SegFormer / PersonMaskUltra) — https://www.reddit.com/r/comfyui/comments/1lpslyr/clothing_segmentation_workflow_help_needed/
4. Connecting Florence2 Captions to SAM2 Masks — https://www.reddit.com/r/comfyui/comments/1f86mum/connecting_florence2_captions_to_sam2_masks_can/
5. I built a simple grounding package (15+ models) — https://www.reddit.com/r/comfyui/comments/1odouse/i_built_a_simple_grounding_package_15_models_3/
6. Apart from SAM2 which prompt-based masking tool? — https://www.reddit.com/r/comfyui/comments/1glmqkp/apart_from_sam2_which_prompt_based_masking_tool/
7. OOTDiffusion (official) — https://github.com/levihsu/ootdiffusion
8. OOTDiffusion paper (AAAI 2025) — https://arxiv.org/pdf/2403.01779
9. IDM-VTON — Just Another Level — https://www.reddit.com/r/StableDiffusion/comments/1ce2iax/idmvton_virtual_tryon_is_just_another_level/
10. Best model for virtual try on — https://www.reddit.com/r/comfyui/comments/1h74itl/best_model_for_virtual_try_on/
11. IDM-VTON mind blowing / ComfyUI nodes — https://www.reddit.com/r/sdforall/comments/1ciu79w/idmvton_virtual_try_on_is_simply_mind_blowing_can/
12. Near Perfect Virtual Try On — https://www.reddit.com/r/StableDiffusion/comments/1k06rrx/near_perfect_virtual_try_on_vton/
13. Virtual Try On accuracy — https://www.reddit.com/r/comfyui/comments/1ka58qq/virtual_try_on_accuracy/
14. How to create model try-on photos — https://www.reddit.com/r/StableDiffusion/comments/1er9s8i/how_to_create_model_try_on_photos_like_this/
15. Virtual try on (body-shape drift / FitDiT) — https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/virtual_try_on/
16. SAL-VTON clothes swap workflow — https://www.reddit.com/r/StableDiffusion/comments/1bhqdro/dress_your_virtual_influencer_comfyui_workflow/
17. Clothes Try-On (Qwen Edit LoRA) + clothing extractor — https://www.reddit.com/r/StableDiffusion/comments/1nbzh2d/clothes_try_on_clothing_transfer_qwen_edit_loraa/
18. Klein or Qwen — https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/klein_or_qwen/
19. Qwen-Image-Edit Prompt Guide — https://www.reddit.com/r/StableDiffusion/comments/1n1n81o/qwenimageedit_prompt_guide_the_complete_playbook/
20. Which model is best for image editing (identity) — https://www.reddit.com/r/StableDiffusion/comments/1tdi287/which_model_is_best_for_image_editing_maintaining/
21. Why "preserve the face" fails in edit models — https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/why_preserve_the_face_prompts_fail_in_edit_models/
22. Best Virtual try-on model? (Fashn leaderboard) — https://www.reddit.com/r/comfyui/comments/1mow8vn/best_virtual_tryon_model/
23. Changing outfits keeping identical character/pose — https://www.reddit.com/r/StableDiffusion/comments/1wb0dt4/need_recommendation_changing_outfits_while/
24. has anyone tried minimax swap only clothes? — https://www.reddit.com/r/StableDiffusion/comments/1wzh4yf/has_anyone_tried_minimax_swap_only_clothes/