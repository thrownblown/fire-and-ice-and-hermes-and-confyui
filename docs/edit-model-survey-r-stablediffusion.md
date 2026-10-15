# Image Edit Models Discussed on r/StableDiffusion — Survey

Survey of instruction-based / reference-based image EDIT models under active
discussion on r/StableDiffusion, compiled 2026-10-15 from Reddit search +
`site:reddit.com` queries (thread bodies/comments pulled via the arctic-shift
archive; dates are the thread's `created_utc`).

Ranked shortlist is at the top; each model gets a section below; a source list
closes the report. Every concrete claim is tied to a linked thread. Anything I
could not tie to a thread is explicitly tagged `(unverified)`.

## Ranked shortlist (top 3)

1. **Qwen-Image-Edit (2509 / 2511)** — the consensus default. Repeatedly called
   "best open-source image editing model by far" and placed 2nd *overall* (behind
   only a closed model) on the Artificial Analysis leaderboard. Strongest
   instruction-following and multi-turn consistency in the community's view.
   Full ComfyUI support; runs on 8 GB via Nunchaku SVDQuant.
2. **Flux 2 Klein (9B distilled)** — the speed + identity pick. 4-step/8-step
   distilled, runs on ~12 GB and below, near-instant edits, and the strongest
   "it's better than any closed model" sentiment threads in late 2025 / 2026. The
   biggest single-ecosystem (LLM tool-calling, one-node wrappers, identity-transfer
   nodes).
3. **Flux Kontext (dev / pro)** — best *precise, minimal* edits and identity
   preservation, per multiple direct comparisons; but slow (~3x), pro is API-only,
   and the recurring complaints are unwanted zoom/crop and resolution kneecapping.

Honorable mentions (detailed below): ACE++, LongCat-Image-Edit/Turbo, FireRed
Image Edit, OmniGen2, Step1X-Edit, ICEdit, HiDream-E1.

---

## Qwen-Image-Edit

- **Kind of edits**: instruction edit; text replacement; subject/reference
  preservation (~"one-shot LoRA" behavior); local inpainting edit; style transfer;
  scene swaps. Strongest reported strength is *prompt adherence on complex edits*
  and multi-turn consistency.
- **Hardware / VRAM**: runs on 8 GB (RTX 3070 laptop, ~37 s) through the Nunchaku
  SVDQuant fp4 backend; ~30 s on a 4060 Ti. Community favors the "Nunchaku"
  ComfyUI backend (listen on port 4567) + fp4 SVDQuant weights.
- **ComfyUI**: yes — official Nunchaku Comfy workflows plus the
  `TextEncodeQwenImageEdit` node; a known workflow gotcha (leave the node's VAE
  UN-connected or the reference latent resizes/crops the input — the node also
  downsamples its reference to ≤1 MP internally).
- **Limitations / complaints**: no access to the model's internal masking, so
  inpainting leaks outside your mask (the #1 complaint thread); frequently weak
  on *text* edits; the edit output can look "AI skin"/artificial and can show
  scanlines/dots vs. Klein; identity preservation is good but not perfect; it is
  effectively a fine-tune of Qwen-Image (2509 added multi-image input via
  concatenation, plus ControlNet; 2511 is the newest).
- **Threads**: release (2025-08-18), 2509 release (2025-09-22), "best open-source
  by far, 2nd overall" (2025-08-20), "I absolutely love Qwen" + hardware notes
  (2025-09-21), "biggest issue" masking (2025-09-16), 2511 vs LLaDA comparison
  (2026-09-08).

## Flux 2 Klein (4B / 9B distilled)

- **Kind of edits**: whole-image style transforms, fine detail edits, outpainting,
  inpainting, face swap, sketch-to-image, upscaling/restoration/colorization,
  object add/remove, relighting, background change, character-dataset generation.
  Community framing: "Qwen does fine detail, Klein does whole-image transforms."
- **Hardware / VRAM**: the most consumer-friendly. 9B-distilled = 8 steps @ CFG 1;
  4B runs alongside an LLM (Mistral-Nemo Q4) *and* does generations on a 24 GB GPU,
  ~5 s per image; LoRA training ~30 min on 12 GB. GGUF quantized versions are the
  standard local route.
- **ComfyUI**: yes — official "Image Edit (Flux.2 Klein)" node/workflow, a
  community "One Node" all-in-one wrapper (T2I/I2I/Edit/Inpaint/Outpaint/Sketch/
  Faceswap), plus Identity-Transfer + subject-mask nodes and a Flux2Klein Enhancer
  node for staged edit strength.
- **Limitations / complaints**: identity can be inconsistent (vs. Qwen 2511) without
  a consistency LoRA/identity-transfer node; a default `ImageScaleToTotalPixels`
  node silently resizes output (mismatched-res bug); repeated edits drift color
  (oversaturated on Klein, muted on the full model); needs the latest ComfyUI +
  updated GGUF node.
- **Threads**: "better than any closed model" (2026-04-19), "most underrated
  editing/upscaling model" (2026-09-11), "The True power" Open-WebUI integration
  (2026-01-16), 5090 local editing (undated, recent), resolution-mismatch fix,
  single ComfyUI node announcement (2026-06-19).

## Flux Kontext (dev / pro)

- **Kind of edits**: *precise* minimal edits ("modify X, retain Y, leave Z
  untouched") — local edit, text/title replacement, background/time-of-day change,
  iterative re-edits with character/style retention, and combining two images into
  one. BFL's stated focus is editing, not text-to-image.
- **Hardware / VRAM**: heavier than Klein; reported ~3x slower than Klein even with
  Nunchaku; `pro` is API-only, `dev` runs locally; constrained to a fixed list of
  resolution buckets and reliably flaky below 1024×1024.
- **ComfyUI**: yes — official Flux Kontext workflows (I2I + regional-prompting
  boxes PSA), `FluxKontextImageScale` node, GGUF route.
- **Limitations / complaints**: the recurring one is unwanted zoom/crop/shift (it
  "re-generates" the image rather than registering 1:1 like instructpix2pix); can
  return the input unchanged for small changes; smaller images make it alter the
  whole picture; no image-as-style-reference (that's Redux's job).
- **Threads**: prompting playbook (2025-08-28), Redux-vs-Kontext (2025-06-26),
  crop/shift complaint (2025-07-02), "great at changing titles" + regional-prompt
  boxes PSA, minimum 1024×1024 (undated).

## ACE++ (Flux Fill LoRA stack)

- **Kind of edits**: instruction edit ("add a bench...", "change her shirt"),
  character-consistency-from-one-image, subject/portrait/local edit — via three
  LoRAs (portrait / subject / local) combined with a Flux Fill base (fp8/fp16).
  Reference-aware: give it a character image and prompt for pose/clothing/background.
- **Hardware / VRAM**: inherits Flux Fill footprint; needs Flux Fill model + ACE++
  LoRAs. On a 4090-class card it is comfortable but not "light."
- **ComfyUI**: yes — Liara/community workflows; commonly paired with FluxFill
  inpainting, since ACE++ *requires* Flux Fill to work.
- **Limitations / complaints**: harder to set up than Kontext/Qwen; local-edit LoRA
  came later than subject/portrait; 768px ceiling noted in the ICEdit/DreamO sibling
  discussion (VACE-style side-by-side processing); face-swap use is "reconstruction/
  regional regen," weak when the reference is low quality.
- **Threads**: character-consistency workflow (2025-01-31), makeup transfer (undated),
  "Flux Kontext alternatives" (2025-07-07), DreamO/Uno/ICEdit comparison (undated).

## LongCat-Image-Edit / Turbo (Meituan, 6B)

- **Kind of edits**: instruction edit with strong face-reference preservation
  ("2nd best for face references after Flux 2 Dev"); single-image inpainting;
  camera-angle edits (below/above); multi-image composition is limited (one image
  at a time in the current release). Uses a Qwen2-VL text encoder, so it reads
  image *structure* during editing.
- **Hardware / VRAM**: 6B dense, ~12.5 GB; Turbo is a rare official 8-step distilled
  *edit* model. ComfyUI route peaks ~27 GB on a 5090 with sageattention/torch
  compile; CPU-offload gets ~35 s/image; FP8 expected to fit <12 GB once natively
  supported.
- **ComfyUI**: yes — community `comfyui_longcat_image` workflow; a native Comfy
  implementation is awaited.
- **Limitations / complaints**: frequent "returns the exact same image" reports;
  struggles with multiple references; camera rotation is limited (subject rotates
  instead of the camera); smaller community footprint than Klein/Qwen.
- **Threads**: "Z-Image Edit basically already here... 8-step Turbo" (2026-02-03),
  samples thread (2026-05-02), ComfyUI workflow thread, "finetune... returns same
  image" (undated).

## FireRed Image Edit

- **Kind of edits**: instruction edit with what several users call the *best*
  identity consistency of the open options tested (identity/face retention across
  edits).
- **Hardware / VRAM**: not specified in the thread cited (unverified).
- **ComfyUI**: installable; the cited thread only confirms model availability, not
  a specific workflow (unverified).
- **Limitations / complaints**: conspicuously under-discussed despite praise — "it's
  surprising it doesn't get more attention."
- **Thread**: "Which model is best for image editing maintaining identity
  consistency" (2026-05-15).

## OmniGen / OmniGen2 (VectorSpaceLab / Stability)

- **Kind of edits**: "just ask for it in natural language" — iterative NL editing,
  character consistency, scene merging, virtual try-on, adding elements
  (instructions like "shorten the dress," "make her smile"). Unified single-model
  text+image control (no ControlNet).
- **Hardware / VRAM**: resource-heavy — ~40 s for 1024² on a 4090, 2–4 min for edit
  tasks, up to ~17 GB VRAM; 48 GB "recommended" is joked about in-thread. Ran on
  CPU by default in early releases (needs explicit CUDA torch + `model.py` edit).
- **ComfyUI**: yes — community node (ComfyUI PR #8669) + gradio; known bugs patched
  from the repo issues.
- **Limitations / complaints**: v1 was "early days / buggy" (syntax & package
  errors, slow); OmniGen2's marketed demos outperform reality — character-consistency
  and virtual try-on failed in a widely-upvoted test; needs seed re-rolls (5–6
  attempts common); output quality ~base-SDXL-to-SD1.5 unless post-processed. Tune
  guidance scale (≥6) + image guidance (~2.5) to keep input attributes.
- **Threads**: release (2024-11, `1g9fimr`), "gap between demos and reality"
  (2025-06-26), numbers/enabling-GPU (undated), "does what o4 does, runs in ComfyUI"
  (undated), OmniEdit (2024-11).

## Step1X-Edit (v2)

- **Kind of edits**: GPT-4o-style instruction edit (multimodal LLM + diffusion
  decoder); single-image editing with strong consistency; face edits can be a
  "draw a card" gamble (InstantID post-swap suggested in-thread). v2 adds reasoning/
  reflection and claims benchmark results above Qwen-Image-Edit-2509.
- **Hardware / VRAM**: fp8 supported; ~100 s/image on a Win 4090; needs 24 GB for
  comfortable fp8 use in the cited writeup. Early builds OOM'd >1024² even on a 4090.
- **ComfyUI**: yes — `ComfyUI_SStep1X` ("ComfyUI-S_1X") custom node.
- **Limitations / complaints**: mixed to negative first impressions ("manage your
  expectations"; "outputs fall far short of claimed quality"; prompting may work
  better in Chinese); early versions effectively Linux-first, Windows lagging.
- **Threads**: "Image Editing in the Style of GPT-4O" (2025-05-14), practical
  framework paper, "change details" first-run report (undated), "at home?" (undated).

## ICEdit

- **Kind of edits**: instruction edit; identity preservation ("promising results with
  identity preservation"); can style/transfer but is reported unable to *remove*
  elements in the version discussed.
- **Hardware / VRAM**: ~14 GB VRAM per the style-transfer thread.
- **ComfyUI**: yes — a Comfy workflow exists (14 GB VRAM), plus a custom-node
  variant; native-node-only runs failed for one user (needs custom ICEdit nodes).
- **Limitations / complaints**: needs better control; the "can't delete elements"
  issue; limited resolution ceiling in the VACE-style family (~768).
- **Threads**: "Best way to apply a Style only to an image?" (undated), DreamO/Uno
  comparison (undated).

## HiDream-E1

- **Kind of edits**: editing model (successor framing via the Step1X-Edit thread's
  "ICEdit and Step1X... or HiDream E1 maybe").
- **Hardware / VRAM**: expected "easier on consumer GPUs" than Step1X-Edit; full
  weights ~32 GB noted (transformer shares weights with full model); GGUF splits
  posted.
- **ComfyUI**: Comfy-Org support flagged as coming; GGUF loader route usable.
- **Limitations / complaints**: very early — no polished workflow when discussed.
- **Thread**: "HiDream-E1 editing model released" (undated).

## Brief honorable mentions

- **Flux Redux** — style/reference variation model, not an editor proper; used as a
  style precondition feeding Kontext, since Kontext can't take an image as *style*
  reference yet (`1llb1iq`).
- **Flux Fill** — inpainting backbone that ACE++ and many masking workflows run on
  top of (`1ieg3p7`, `1raurkj`).
- **LLaDA-Image-Turbo** — new lightweight contender; loses to Qwen-Image-Edit-2511
  in a Sept-2026 head-to-head (`1wai459`).
- **InstructPix2Pix / SDXL inpainting** — legacy names; now referenced mainly as the
  "registers pixels 1:1" contrast against Kontext's re-generation behavior
  (`1lq0pxv`). Not separately championed in current threads (unverified).
- **DreamO / Uno** — Flux-Dev one-shot customization LoRAs (not editors) (`1khxpms`).
- **Krea 2 / Z-Image / Qwen JS / Ideogram 4 / Flux 2 Dev** — named in "what model do
  you use nowadays" roundups (`1ui8cir`, `1w3a772`); Krea 2 is closed and praised for
  edit quality, Z-Image for skin/speed.

---

## Sources (Reddit threads, newest→oldest)

- https://www.reddit.com/r/StableDiffusion/comments/1wdh0l0/ — Flux2Klein most underrated (2026-09-11)
- https://www.reddit.com/r/StableDiffusion/comments/1wai459/ — Qwen-Image-Edit-2511 vs LLaDA-Image-Turbo (2026-09-08)
- https://www.reddit.com/r/StableDiffusion/comments/1tdi287/ — best for identity consistency (2026-05-15)
- https://www.reddit.com/r/StableDiffusion/comments/1t1asrc/ — Longcat-Image-Edit samples (2026-05-02)
- https://www.reddit.com/r/StableDiffusion/comments/1spq72f/ — Flux Klein better than any closed model (2026-04-19)
- https://www.reddit.com/r/StableDiffusion/comments/1qurc2w/ — LongCat 8-step Turbo (2026-02-03)
- https://www.reddit.com/r/StableDiffusion/comments/1qetwgf/ — True power of Flux.2 Klein (2026-01-16)
- https://www.reddit.com/r/StableDiffusion/comments/1nnt6o5/ — Qwen-Image-Edit-2509 released (2025-09-22)
- https://www.reddit.com/r/StableDiffusion/comments/1nn51kn/ — I absolutely love Qwen (2025-09-21)
- https://www.reddit.com/r/StableDiffusion/comments/1nijl03/ — biggest issue with Qwen-Edit (2025-09-16)
- https://www.reddit.com/r/StableDiffusion/comments/1n253n7/ — Flux Kontext Prompting Playbook (2025-08-28)
- https://www.reddit.com/r/StableDiffusion/comments/1mvni4c/ — Qwen best open-source, 2nd overall (2025-08-20)
- https://www.reddit.com/r/StableDiffusion/comments/1mtt29y/ — Qwen-Image-Edit released (2025-08-18)
- https://www.reddit.com/r/StableDiffusion/comments/1ltwkpu/ — Flux Kontext alternatives (2025-07-07)
- https://www.reddit.com/r/StableDiffusion/comments/1lq0pxv/ — Kontext crop/shift (2025-07-02)
- https://www.reddit.com/r/StableDiffusion/comments/1llb1iq/ — Flux Redux vs Kontext (2025-06-26)
- https://www.reddit.com/r/StableDiffusion/comments/1lkuk57/ — OmniGen2 demos vs reality (2025-06-26)
- https://www.reddit.com/r/StableDiffusion/comments/1kmml04/ — Step1X-Edit GPT-4o style (2025-05-14)
- https://www.reddit.com/r/StableDiffusion/comments/1ieg3p7/ — ACE++ character consistency (2025-01-31)
- https://www.reddit.com/r/StableDiffusion/comments/1g9fimr/ — OmniGen released (2024-11)

Additional supporting threads (undated roundups/comparisons):
- https://www.reddit.com/r/StableDiffusion/comments/1ui8cir/ — latest & greatest image model roundup
- https://www.reddit.com/r/StableDiffusion/comments/1w3a772/ — what image edit model nowadays
- https://www.reddit.com/r/StableDiffusion/comments/1ubedvu/ — is Flux Klein still best
- https://www.reddit.com/r/StableDiffusion/comments/1uwm6c7/ — local editing on a 5090
- https://www.reddit.com/r/StableDiffusion/comments/1u9g3vy/ — single ComfyUI node for FLUX.2 klein
- https://www.reddit.com/r/StableDiffusion/comments/1qf2ci7/ — Flux-2-klein sketches
- https://www.reddit.com/r/StableDiffusion/comments/1qgsbz3/ — Flux Klein vs Kontext for editing
- https://www.reddit.com/r/StableDiffusion/comments/1pc18wl/ — Step1X-Edit framework
- https://www.reddit.com/r/StableDiffusion/comments/1m2tvfh/ — ACE++ makeup transfer
- https://www.reddit.com/r/StableDiffusion/comments/1khxpms/ — DreamO/Uno/ICEdit comparison
- https://www.reddit.com/r/StableDiffusion/comments/1k9zrxu/ — HiDream-E1 released