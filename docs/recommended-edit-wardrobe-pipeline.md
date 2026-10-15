# Recommended Edit + Wardrobe Pipeline — FNI

Synthesis of three sibling research reports:
- *Edit-model survey* (r/StableDiffusion) — `edit-model-survey-r-stablediffusion.md`
- *ComfyUI edit workflows* (r/comfyui) — `research-comfyui-edit-workflows.md`
- *Wardrobe extraction & replacement* — `research-wardrobe-extraction-replacement.md`

Compiled 2026-10-15. Every concrete claim carries a source link (see the source index at
the bottom) or an explicit `(unverified)` tag. This document is meant to be followed without
reading the three underlying reports.

---

## 1. Executive summary

The OpenSources community has converged on three edit-model families — **Qwen-Image-Edit**
(the default instruction-edit model, best at face/identity and prompt adherence), **Flux Kontext**
(best at *precise, minimal* edits but slow and prone to zoom/crop drift), and **Flux 2 Klein**
(the fast, fabric-realistic, low-VRAM option for whole-image transforms). For the two FNI jobs:
**(a) edit an existing image** → run Qwen-Image-Edit FP8 as primary with Flux Kontext dev as the
precise-edit fallback; **(b) extract a garment + replace clothing** → segment with
**Florence-2 + SAM2** (SegFormer clothing parser as photo fallback), then inpaint with
**Flux.1 Fill + Redux + ACE++** (Qwen-Edit try-on LoRA / Klein as secondaries), with a mandatory
face-detail identity pass after any torso-touching re-render. The single decision that matters
most at every VRAM tier is **quantization** (FP8 when ~22 GB fits, GGUF Q4–Q8 otherwise, GGUF
Q2/Q3 as the 2–6 GB floor), and the single most common beginner trap is **turbo/distilled LoRAs,
which deep-fry edited skin** — avoid them. For the downstream H3 video stage, the wardrobe
replacement must first produce a *reference still of the character already wearing the target
outfit*; prose-only clothing swaps revert in MiniMax video the vast majority of the time.

---

## 2. Reconciled consensus & where the reports disagree

### Points all three reports agree on (high confidence)

- **Qwen-Image-Edit is the default open edit model.** Called "best open-source image editing
  model by far," 2nd overall behind a closed model on the Artificial Analysis leaderboard
  ([1](https://www.reddit.com/r/StableDiffusion/comments/1mvni4c/)); strongest instruction-following
  and multi-turn consistency ([1](https://www.reddit.com/r/StableDiffusion/comments/1mvni4c/),
  [2](https://www.reddit.com/r/StableDiffusion/comments/1nn51kn/)).
- **Qwen is best at character likeness / identity; Klein is best at fabric realism and speed.**
  The comfyui survey: "Qwedit is best at character likeness… Klein 9B better/faster at many
  general edits but weaker on likeness" ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/)).
  The wardrobe survey independently: Klein has "the best natural fabric/identity… better than
  Qwen-Edit on fabric realism," while Qwen output skews toward "plastic/artificial skin"
  ([4](https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/)).
- **Distilled / turbo / lightning LoRAs deep-fry edited faces.** Warned against in both the
  comfyui failure-mode list ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/)) and the edit
  survey's Klein/Qwen sections ([5](https://www.reddit.com/r/comfyui/comments/1rdkqle/)).
- **Kontext is the precise-minimal-edit pick but re-generates rather than registers 1:1**
  (the recurring zoom/crop/shift complaint) ([6](https://www.reddit.com/r/StableDiffusion/comments/1lq0pxv/),
  [7](https://www.reddit.com/r/StableDiffusion/comments/1n253n7/)).

### Where the reports appear to disagree (and how to read it)

1. **"Qwen is #1" vs "Klein beats everything."** The edit survey ranks Qwen first, Klein second;
   separate Klein threads claim "better than any closed model" ([8](https://www.reddit.com/r/StableDiffusion/comments/1spq72f/)).
   This is not a real contradiction — they measure different axes. Qwen wins on *face/identity +
   instruction adherence*; Klein wins on *fabric realism, speed, and VRAM headroom*. For FNI's
   wardrobe use case (clothing, not faces being changed) the wardrobe report and the comfyui
   survey actually agree that both work, with Klein stronger on the clothing texture itself
   ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/), [4](https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/)).
2. **Qwen's masking/removal weakness is described two ways.** The edit survey calls it "no access
   to internal masking → inpainting leaks outside your mask" ([9](https://www.reddit.com/r/StableDiffusion/comments/1nijl03/));
   the comfyui survey has a "doesn't remove anything" workflow thread ([10](https://www.reddit.com/r/comfyui/comments/1pul8b3/)).
   Both point the same way: **Qwen-Edit is not a reliable inpainter — do localized removal/swap
   with a real inpainting pass (Flux Fill / CropAndStitch), not an instruction prompt.**
3. **VRAM numbers look different but reconcile.** The edit survey says Qwen runs on 8 GB via
   Nunchaku SVDQuant fp4 (~37 s on a 3070 laptop) ([2](https://www.reddit.com/r/StableDiffusion/comments/1nn51kn/));
   the comfyui survey says Qwen FP8 = 22 GB, GGUF Q4–Q8 = 8–12 GB ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/)).
   These are *three different precision paths* (fp4 SVDQuant / FP8 / GGUF), not a conflict.
   Credibility note: the comfyui survey's table is more precise about node packs and is the
   better guide for wiring the workflow; the edit survey's 8 GB claim is about the Nunchaku path
   specifically.
4. **Klein identity: "inconsistent" vs "holds identity well on clothing edits."** The edit survey
   flags identity inconsistency vs Qwen 2511 without a consistency LoRA ([11](https://www.reddit.com/r/StableDiffusion/comments/1tdi287/));
   the wardrobe survey clarifies the audit — Klein drifts on *pose/expression* changes but holds
   identity well for *clothing* changes specifically, because the face stays largely untouched
   ([12](https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/)). Read the wardrobe survey as
   the more applicable finding for FNI; the edit survey's caveat is about whole-scene identity.

---

## 3. Recommended stack A — "edit an existing image"

Target rig: 4090 (24 GB) restyle box, or the 5090 for heavy FP8 work.

| Role | Choice | Node packs / notes | Source |
|---|---|---|---|
| Primary instruction edit | **Qwen-Image-Edit (FP8, 2511)** | Native nodes + `ComfyUI_LayerStyle` (scale) + optional `ComfyUI-SeedVR2` upscale; **double-ref trick** (feed reference twice, control input scale/output size) to fix soft edits | [3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/) |
| Precise / minimal edits | **Flux Kontext [dev]** | Native ComfyUI templates (day-0, no custom nodes); `FluxKontextImageScale` node | [13](https://www.reddit.com/r/comfyui/comments/1ll3emk/), [7](https://www.reddit.com/r/StableDiffusion/comments/1n253n7/) |
| Fast / low-VRAM alternative | **Flux 2 Klein (4B/9B, GGUF)** | `ComfyUI-GGUF`, Flux2 CLIP/VAE loaders, official Image Edit node | [14](https://www.reddit.com/r/comfyui/comments/1rdkqle/), [15](https://www.reddit.com/r/StableDiffusion/comments/1u9g3vy/) |
| Localized fixes (garment/face swap) | inpainting pass | `ComfyUI-Inpaint-CropAndStitch` (full-res masked region) | [16](https://www.reddit.com/r/comfyui/comments/1rkfwpn/) |
| Structural / pose transfer | ControlNet | InstantX Union (Qwen) / FLUX.2 Union via `JLC-ControlNet Orchestrator` | [17](https://www.reddit.com/r/comfyui/comments/1vfr9js/) |

**Known gotchas that must be observed (all sourced):**

- Multi-image Qwen prompts use the literal `Picture 1: <desc>. Picture 2: <desc>.` prefix; the
  model misattributes inputs otherwise ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/)).
- **ReferenceLatent + ControlNet cannot be combined on Qwen** — tensor-shape mismatch; pick one
  conditioning path ([18](https://www.reddit.com/r/comfyui/comments/1n5w5lw/)).
- **Negative prompts are ignored at CFG ≤ 1.0** (Qwen/Klein/Kontext) — put everything in the
  positive prompt, leave the negative node blank ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/) `(see Pattern 7)`).
- A text-only prompt change can balloon Qwen edit time from 10 s to 20 min (full VL text encoder
  re-encode + cache reset); keep VRAM ≤ 90–95 %, move the encoder to CPU, or use an FP8 encoder
  ([19](https://www.reddit.com/r/comfyui/comments/1o6e1qa/)).

---

## 4. Recommended stack B — "extract garment + replace clothing"

### 4a. Extraction (garment cutout / mask)

| Rank | Approach | Node packs / models | Notes | Source |
|---|---|---|---|---|
| 1 | **Florence-2 + SAM2** | Kijai `segment-anything-2` + `ComfyUI-Florence2` | Open-vocab semantic masking; current community default; isolates one person among several by cascade | [20](https://www.reddit.com/r/comfyui/comments/1f86mum/), [21](https://www.reddit.com/r/comfyui/comments/1odouse/) |
| 2 | **SegFormer clothing parser** | `ComfyUI_LayerStyle` → **PersonMaskUltra V2**; `segformer_b2_clothes`/`b3_fashion` HF models | Most reliable per-image on real photos (no text prompt needed); invert-selection trick for garment classes | [22](https://www.reddit.com/r/comfyui/comments/1lpslyr/) |
| 3 | **GroundingDINO + SAM / SAM-HQ** | `comfyui_segment_anything` (storyicon) | Mature text-prompt→box→mask; ~1/3 success on clothing specifically, needs mask add/subtract cleanup | [23](https://www.reddit.com/r/StableDiffusion/comments/13old1j/), [24](https://www.reddit.com/r/comfyui/comments/18wuacc/) |

**Cleanup idiom (every report repeats it):** segment a *broader* region (upper body) and subtract
hands/face — hair and skin are detected more reliably than cloth — then a small erode/dilate
([23](https://www.reddit.com/r/StableDiffusion/comments/13old1j/), [20](https://www.reddit.com/r/comfyui/comments/1f86mum/)).

### 4b. Replacement (clothing swap)

| Rank | Approach | Node packs / models | Notes | Source |
|---|---|---|---|---|
| 1 | **Flux.1 Fill + Redux (+ ACE++)** | Native Flux Fill + Redux + ACE++ subject LoRA | Mask-inpaint; pose/background stable; feed the step-4a cutout as Redux reference or joycaption the garment; community "gets you 90 %" | [25](https://www.reddit.com/r/StableDiffusion/comments/1k06rrx/), [26](https://www.reddit.com/r/comfyui/comments/1ka58qq/), [27](https://www.reddit.com/r/comfyui/comments/1h74itl/) |
| 2 | **Qwen-Image-Edit try-on / "clothing extractor" LoRA** | Standard Qwen-Edit + LoRA swapped in | Already in FNI's stack; pose-stable but watch plastic skin → identity pass | [28](https://www.reddit.com/r/StableDiffusion/comments/1nbzh2d/), [29](https://www.reddit.com/r/StableDiffusion/comments/1n1n81o/) |
| 2 (alt) | **Flux.2 Klein 9B** | Official Klein Image Edit + ComfyUI-GGUF | Best fabric realism; mask + "keep everything else consistent" phrasing + paste-by-mask compositing | [4](https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/) |
| 3 | **IDM-VTON** | `ComfyUI-IDM-VTON` (TemryL) | Best raw try-on accuracy, but **non-commercial license** + upper-body-only → *do not ship*; trial-only | [30](https://www.reddit.com/r/StableDiffusion/comments/1ce2iax/), [31](https://www.reddit.com/r/sdforall/comments/1ciu79w/) |
| fallback | CatVTON / OOTDiffusion / FitDiT | `Comfyui-CatVTON` … | Lightweight/full-body/low-VRAM alternatives; pose drift & low-res (CatVTON), body-shape drift (FitDiT/OOT) | [32](https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/), [33](https://github.com/levihsu/ootdiffusion) |

**Mandatory identity pass after any torso-touching re-render:** face detailer / faceswap against a
neutral headshot, masked to the face. The "preserve the face" prompt *does not work* in edit
models — the face stays intact only when masked out or re-asserted in a separate pass
([34](https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/)). Follow with upscale/seam-fix
(UltimateSDUpscale / ESRGAN or a Flux-Kontext seams pass) to blend the inpaint boundary
([16](https://www.reddit.com/r/comfyui/comments/1rkfwpn/)).

### 4c. The MiniMax H3 handoff (critical for FNI)

A r/StableDiffusion test of swapping *only* clothing in MiniMax video reported **under 50 % success**:
the outfit reverted to the original after ~5–6 s unless (a) a dedicated reference image of the
character *already in the new outfit* was supplied, or (b) the retention-analysis / subject-definition
prompt fields explicitly re-stated the new clothing each time. **Practical rule: for H3 video,
first produce a "character in desired outfit" reference still via §4a/§4b, then feed that still as
the subject reference — never try to swap clothes with prose alone.**
([35](https://www.reddit.com/r/StableDiffusion/comments/1wzh4yf/))

---

## 5. VRAM tiers (lowest viable per job)

| VRAM | Edit an image | Extract garment | Replace clothing |
|---|---|---|---|
| 2–6 GB | Klein 4B Q2/Q3 GGUF ([14](https://www.reddit.com/r/comfyui/comments/1rdkqle/)) | GroundingDINO + SAM ViT-B (light) ([24](https://www.reddit.com/r/comfyui/comments/18wuacc/)) | Klein 4B inpaint; CatVTON (lightest VTON) ([32](https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/)) |
| 8 GB | Qwen Edit fp4 (Nunchaku SVDQuant) / Kontext int4 ([36](https://www.reddit.com/r/comfyui/comments/1ms8t97/), [2](https://www.reddit.com/r/StableDiffusion/comments/1nn51kn/)) | Florence-2 + SAM2 (few GB, not bottleneck) ([20](https://www.reddit.com/r/comfyui/comments/1f86mum/)) | FitDiT (~8 GB) ([32](https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/)) |
| 12 GB | Klein 9B GGUF Q4 / Qwen GGUF Q3–Q4 ([37](https://www.reddit.com/r/comfyui/comments/1vfdrf3/)) | SegFormer parser (low) ([22](https://www.reddit.com/r/comfyui/comments/1lpslyr/)) | Flux Fill + Redux (8–16 GB toleranced) ([27](https://www.reddit.com/r/comfyui/comments/1h74itl/)) |
| 22–24 GB (4090/5090) | Qwen FP8; Kontext dev full | — | Flux.1 Fill + Redux + ACE++; IDM-VTON (~16 GB) ([27](https://www.reddit.com/r/comfyui/comments/1h74itl/), [30](https://www.reddit.com/r/StableDiffusion/comments/1ce2iax/)) |

Rule of thumb below 24 GB: text encoder on CPU (or FP8 encoder), lowest quantization that holds
acceptable quality ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/)).

---

## 6. What to try first (quickstart)

**Cheapest single-still wardrobe edit, ≤ 30 min on the 4090:**
SegFormer mask (PersonMaskUltra V2) → **Qwen-Image-Edit** try-on LoRA → face detailer
([22](https://www.reddit.com/r/comfyui/comments/1lpslyr/), [28](https://www.reddit.com/r/StableDiffusion/comments/1nbzh2d/)).

**Best open-quality identity + pose fidelity:**
Florence-2/SAM2 mask → **Flux.1 Fill + Redux + ACE++** → face detailer → upscale/seam-fix
([20](https://www.reddit.com/r/comfyui/comments/1f86mum/), [25](https://www.reddit.com/r/StableDiffusion/comments/1k06rrx/)).

**First move on the edit-pipeline generally:**
Install `ComfyUI-GGUF`, `ComfyUI_LayerStyle`, `ComfyUI-Inpaint-CropAndStitch`, and
`segment-anything-2` + `ComfyUI-Florence2` — those four packs cover every path above. Pin a seed
and run one Qwen-Edit FP8 instruction edit with the double-ref trick before committing to a model
family ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/)).

---

## 7. Open questions / gaps (thin community evidence)

1. **"Preserve-the-face"/negative-prompt behavior is anecdotal, not measured.** The claims that
   negative prompts are ignored at CFG ≤ 1.0 and that preserve-the-face prose fails are consistent
   across threads but lack a controlled comparison ([3](https://www.reddit.com/r/comfyui/comments/1tqm4pb/),
   [34](https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/) `(unverified beyond anecdotes)`).
2. **No clean-garment-cutout solution exists.** Every extraction route needs per-image mask
   add/subtract cleanup; "extract just the outfit, cleanly, automatically" is an unsolved gap with
   no championed tool ([23](https://www.reddit.com/r/StableDiffusion/comments/13old1j/),
   [20](https://www.reddit.com/r/comfyui/comments/1f86mum/)).
3. **FireRed edit-model VRAM & ComfyUI workflow are undocumented.** Praised for identity but the
   cited thread gives no hardware numbers or a specific node pack ([38](https://www.reddit.com/r/StableDiffusion/comments/1tdi287/) `(unverified)`).
4. **Lower-body/dress try-on has no strong open option.** IDM-VTON is upper-body-only; OOTDiffusion
   does full body but is ranked below IDM/CatVTON in every thread ([33](https://github.com/levihsu/ootdiffusion),
   [31](https://www.reddit.com/r/sdforall/comments/1ciu79w/)). For FNI characters with loincloths/tunics
   this is the single most relevant unproven area.
5. **The MiniMax <50 % wardrobe-swap finding is a single thread** — high stakes but n=1; it should
   be re-verified against FNI's own H3 rig before being treated as law
   ([35](https://www.reddit.com/r/StableDiffusion/comments/1wzh4yf/) `(unverified beyond the one test)`).
6. **Qwen vs Klein head-to-head on *clothing specifically* is under-sampled.** The "Klein or Qwen"
   thread is one of the few direct comparisons; a competing Sept-2026 head-to-head put Qwen 2511
   over a different lightweight model (LLaDA), not Klein ([4](https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/),
   [39](https://www.reddit.com/r/StableDiffusion/comments/1wai459/)).

---

## 8. Source index

1. Qwen best open-source / 2nd overall — https://www.reddit.com/r/StableDiffusion/comments/1mvni4c/
2. "I absolutely love Qwen" + hardware notes — https://www.reddit.com/r/StableDiffusion/comments/1nn51kn/
3. Qwen Edit 2511 max-quality deep-dive (double-ref, quant table, failure modes) — https://www.reddit.com/r/comfyui/comments/1tqm4pb/
4. Klein or Qwen (fabric realism) — https://www.reddit.com/r/StableDiffusion/comments/1rjrr3d/
5. Klein 9B GGUF low-VRAM workflows — https://www.reddit.com/r/comfyui/comments/1rdkqle/
6. Kontext crop/shift complaint — https://www.reddit.com/r/StableDiffusion/comments/1lq0pxv/
7. Flux Kontext prompting playbook — https://www.reddit.com/r/StableDiffusion/comments/1n253n7/
8. Flux Klein better than any closed model — https://www.reddit.com/r/StableDiffusion/comments/1spq72f/
9. Biggest issue with Qwen-Edit (masking) — https://www.reddit.com/r/StableDiffusion/comments/1nijl03/
10. Qwen Edit 2511 "doesn't remove anything" — https://www.reddit.com/r/comfyui/comments/1pul8b3/
11. Best for identity consistency — https://www.reddit.com/r/StableDiffusion/comments/1tdi287/
12. Why "preserve the face" fails — https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/
13. Flux Kontext day-0 native support — https://www.reddit.com/r/comfyui/comments/1ll3emk/
14. Klein 9B GGUF low-VRAM (Q2/Q3 floor) — https://www.reddit.com/r/comfyui/comments/1rdkqle/
15. Single ComfyUI node for FLUX.2 Klein — https://www.reddit.com/r/StableDiffusion/comments/1u9g3vy/
16. "Edit like Nano Banana on 3060 12 GB" (CropAndStitch) — https://www.reddit.com/r/comfyui/comments/1rkfwpn/
17. FLUX.2 ControlNet workflow — https://www.reddit.com/r/comfyui/comments/1vfr9js/
18. Qwen ReferenceLatent + ControlNet unsupported — https://www.reddit.com/r/comfyui/comments/1n5w5lw/
19. Qwen Edit 10 s → 20 min slowdown — https://www.reddit.com/r/comfyui/comments/1o6e1qa/
20. Florence-2 captions → SAM2 masks — https://www.reddit.com/r/comfyui/comments/1f86mum/
21. Grounding package (15+ models) — https://www.reddit.com/r/comfyui/comments/1odouse/
22. Clothing segmentation / SegFormer / PersonMaskUltra V2 — https://www.reddit.com/r/comfyui/comments/1lpslyr/
23. Segmentation of a person's clothing — https://www.reddit.com/r/StableDiffusion/comments/13old1j/
24. auto masking (HQ-SAM + GroundingDINO) — https://www.reddit.com/r/comfyui/comments/18wuacc/
25. Near Perfect Virtual Try-On (VTON) — https://www.reddit.com/r/StableDiffusion/comments/1k06rrx/
26. Virtual try-on accuracy — https://www.reddit.com/r/comfyui/comments/1ka58qq/
27. Best model for virtual try-on — https://www.reddit.com/r/comfyui/comments/1h74itl/
28. Clothes try-on Qwen Edit LoRA + clothing extractor — https://www.reddit.com/r/StableDiffusion/comments/1nbzh2d/
29. Qwen-Image-Edit prompt guide — https://www.reddit.com/r/StableDiffusion/comments/1n1n81o/
30. IDM-VTON "just another level" — https://www.reddit.com/r/StableDiffusion/comments/1ce2iax/
31. IDM-VTON mind-blowing / ComfyUI nodes — https://www.reddit.com/r/sdforall/comments/1ciu79w/
32. Virtual try-on (body-shape drift / FitDiT / CatVTON) — https://www.reddit.com/r/StableDiffusion/comments/1irwfqh/
33. OOTDiffusion (official repo) — https://github.com/levihsu/ootdiffusion
34. Why "preserve the face" prompts fail in edit models — https://www.reddit.com/r/StableDiffusion/comments/1v1xchf/
35. MiniMax swap-only-clothes test — https://www.reddit.com/r/StableDiffusion/comments/1wzh4yf/
36. Nunchaku SVDQuant INT4 on 8 GB — https://www.reddit.com/r/comfyui/comments/1ms8t97/
37. Flux Klein instead of Qwen Edit (first-workflow setup) — https://www.reddit.com/r/comfyui/comments/1vfdrf3/
38. Which model is best for editing (identity, FireRed) — https://www.reddit.com/r/StableDiffusion/comments/1tdi287/
39. Qwen-Image-Edit-2511 vs LLaDA-Image-Turbo — https://www.reddit.com/r/StableDiffusion/comments/1wai459/