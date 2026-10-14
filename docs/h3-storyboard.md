# Storyboards / sketch → plate pipeline (4090)

Source thread: r/comfyui 1phrkgy "Does anyone have a good way to create storyboards?" (higgs8,
2025-12-08, 18 comments). Pulled 2026-10-12.

The thread's value is the OP's own follow-up months later, after trying everything.

## What people tried
- **Qwen Image Edit 2509** — converts even "abysmal squiggles" into images (infearia). Add the
  Multiple Angles LoRA (`dx8152/Qwen-Edit-2509-Multiple-angles`) for framing changes and
  `lovis93/next-scene-qwen-image-lora-2509` ("Next Shot") for the next setup. OP's own experience:
  asking Qwen edit to "make the drawing better" does nothing.
- **Multi-pane prompt trick** (sci032) — one prompt, Z-Image Turbo, no controlnet: "create a 4 pane
  storyboard. the panes are equal size. black and white drawing style. the background is a park /
  Pane 1: ... Pane 2: ...". Cheapest storyboard-bloc approach; panes are literal, not sequential.
- **Flux/SDXL + ControlNet** (Southern-Chain-6485): "turn this sketch into a character doing this in
  this place".

## The answer the OP landed on
> "I use Z image Turbo with the omni controlnet, works pretty well! I draw the image badly, write a
> prompt, and let the model figure out how to draw it properly."

Model: **`alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union`** — a single 3.10 GB union Safetensors
(canny / depth / hed / pose in one file, per the repo's asset examples).

## Local setup on this box (the 4090) — verified 2026-10-12
- ComfyUI: `C:\Users\gsfny\venvcomfyui\ComfyUI`, **version 0.39.0**.
- Models: `extra_model_paths.yaml` → `E:/comfymodels/` with `is_default: true`.
- **Core already supports the workflow**: `comfy_extras/nodes_model_patch.py` defines
  `ZImageFunControlnet` (aliases: "z-image controlnet", "controlnet union", "fun controlnet"),
  taking `model` + `model_patch` + `vae` + `strength` (+ optional `image`/`inpaint_image`/`mask`/
  `start_percent`/`end_percent`).
- Z-Image Turbo bases are already present: `E:/comfymodels/models/diffusion_models/zit/` has
  `z_image_turbo_bf16.safetensors`, `zImageTurboAIO_zImageTurboBF16AIO.safetensors`,
  `zimageTurboByStable_2601Bf16.safetensors`, plus fine-tunes.
- `comfyui_controlnet_aux` is installed (canny/hed/depth/pose preprocessors) if we want to derive a
  control image from a still rather than a sketch.
- **MISSING — the one file that makes it work:**
  `Z-Image-Turbo-Fun-Controlnet-Union.safetensors` (3.10 GB), from
  `huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union`.
  `E:/comfymodels/models/controlnet/` is EMPTY, and more importantly it is **not** a controlnet-dir
  file: `ZImageFunControlnet` consumes a `MODEL_PATCH` produced by **`ModelPatchLoader`**, which
  reads `folder_paths["model_patches"]` → the file belongs in
  **`E:/comfymodels/models/model_patches/`**.
  Graph shape: `Load Model Patch → ZImageFunControlnet (model, model_patch, vae, strength, image)`.

## Why this matters for FNI
This is the missing mechanism for **master plates**. The v3.1 plan needs one generated plate per
setup (S05-A/B/C, S06-A..E, ...). Right now a plate would be a pure prompt-and-hope generation.
With this pipeline Alex can:
1. draw the rough setup (framing, subject placement, camera height) as a bad sketch,
2. write the plate prompt (environment only, no characters),
3. get a controlled plate that matches the intended composition,
and it runs on the **4090** — a small image model, not the H3 stack, so it does not compete with the
5090's render queue and is safe to run alongside nothing else heavy.

Caveat: Z-Image Turbo is a small fast model, but it is still a GPU job on the 4090 — do not run it
while LM Studio is loaded on the same card.

## Second thread: "Attempts on next-scene-qwen-image-lora-2509" (r/comfyui 1o81vyt)
https://www.reddit.com/r/comfyui/comments/1o81vyt/attempts_on_nextsceneqwenimagelora2509/
Inevitable_Bag1945, 2025-10-16, 60 up, 30 comments. Pulled 2026-10-12.

**Verdict on the LoRA: skip it.** goddess_peeler ran the controlled A/B — same seed, same workflow,
with and without `lovis93/next-scene-qwen-image-lora-2509` — and posted both: "There's hardly any
difference. Qwen Edit 2509 seems to be doing all the heavy lifting. Prove me wrong." The OP himself:
"the effect is still not stable enough" and "it can be used for entertainment, but it is still a bit
far from being truly practical." Another user: it "heavily tends to introduce black borders."

**Verdict on the TECHNIQUE: steal it.** This is the storyboard loop people actually got working:
1. Take one image (or generate one).
2. Feed it to an **LLM** with: *"Based on this picture, help me come up with a story and include the
   shot information. Separate the prompts between each shot with a carriage return. There's no need
   to explain information like shot one or shot two. Just output it directly. There should be no
   less than 10 story shots."*
3. Each line comes back as `Next Scene: <camera move/reveal>` — the OP's examples are all
   "Next Scene: The camera DOLLY moves right, revealing X" / "tilts up, transitioning from X to Y" /
   "tracks forward, following X as it ..." / "pans left, capturing X" / "pulls back to a wide shot".
4. Generate each prompt in sequence, each new frame becoming the next "current image".

The LLM step is a local model for us — LM Studio on the 4090, which is where this whole thread's
workflow already runs (`goddess_peeler`'s workflow literally uses an LM Studio node:
`https://files.catbox.moe/184720.json`). Base workflow:
`huggingface.co/lovis93/next-scene-qwen-image-lora-2509/blob/main/workflow-comfyui-basic-next-scene.json`.

**FNI relevance:** this is a shot-chain generator — an LLM turns one still into a numbered list of
camera moves and reveals. That is exactly what our `motion[]` / `shot_type[]` / `angle[]` ledger
fields encode by hand, and it is the natural way to draft a *new* sequence (or to sanity-check that
our S05 shot list is a coherent chain). It does NOT replace our setup analysis — it generates
plausible next shots, not the film's actual shots — but as a drafting tool it is cheap (local LLM,
no GPU render). Note the thread's own warnings: the chain drifts, and characters/worldstop do not
stay consistent without a source-of-truth (which is what our plates and refs are for).

## Next step (done 2026-10-12)
- The 3.10 GB union Safetensors was downloaded to
  `E:/comfymodels/models/model_patches/Z-Image-Turbo-Fun-Controlnet-Union.safetensors`
  (3,101,572,408 bytes — matches the HF size; header parses, 136 `control_*` tensors).
- `tools/plate_sketch.py` builds the plate graph (see that file's docstring) from ComfyUI's own
  blueprint and can dry-run, upload a sketch, queue, and wait. Graph validated in dry-run:
  UNETLoader(`zit/z_image_turbo_bf16`) + CLIPLoader(`Qwen3-4B-abliterated`, type `lumina2`)
  + VAELoader(`ae`) + ModelPatchLoader(union) → ZImageFunControlnet → ModelSamplingAuraFlow(3)
  → KSampler(res_multistep/simple, 8 steps, cfg 1) → VAEDecode → SaveImage.
- No extra VAE or text-encoder download is strictly needed: `ae.safetensors` is already the Z-Image
  VAE and the box's Qwen3-4B is the same base as the official `qwen_3_4b.safetensors`.
- Test sketch written to `plates/sketches/TEST_room_sketch.png`; graph at `plates/graphs/TEST_room.json`.
- **Remaining step: start ComfyUI on the 4090** — it is not running (127.0.0.1:8188 refused), and
  LM Studio currently holds ~3.9 GB of the 4090's 24 GB. Run the sketch once that is clear.
