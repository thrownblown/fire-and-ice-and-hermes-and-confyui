# H3 shared links — 2026-10-12 (digest)

Four links shared by Alex. Digest + FNI relevance. Not previously indexed.

---

## A. NimbleCloud13 — "ComfyUI + MiniMax H3: what everything actually does"
- Post: https://www.reddit.com/r/StableDiffusion/comments/1x22omv/comfyuiminimax_cheat_sheet_for_beginners_now_with/
  ("ComfyUI/Minimax Cheat Sheet for Beginners — now with 83% less slop!", 790 upvotes)
- Repo: https://github.com/nimblecloud13/ComfyUI-MiniMax-H3-Guide (54 stars; PDF + self-contained HTML;
  also Wan 2.2 / Qwen Image 2.1 / Krea 2 guides)
- Local copy of the H3 HTML: `explore/h3-field-guide/ComfyUI_MiniMax_H3_Guide.html`
- Plain-English field guide, written for a 16 GB / 32 GB machine, cross-checked against the ComfyUI
  H3 docs, the Comfy-Org/MiniMax-H3 file list and the MiniMax H3 model card (Oct 2026). The most
  concrete "what does this knob do" reference we have — worth using as our settings source-of-truth.

### Modes
- Five modes, two model files: `fl2va` covers T2VA / I2VA / FL2VA / L2VA (one node, `MiniMax H3 Image
  to Video`); `ref2va` is its own file + node (`MiniMax H3 Reference to Video`). Mode is chosen purely
  by what you plug in.
- Ref2VA accepts **up to 9 pictures, 3 clips, 3 audio clips**; refs are examples, not frames.
- First frame = opening shot pixel-for-pixel; a reference = "this person, elsewhere". Tag refs in the
  prompt by plug order: `<Picture 1> <Video 1> <Audio 1>`.
- **Faces need to be close:** H3 holds a face in close-ups and loses it in wide shots. If identity
  matters, frame close. (Directly relevant to our wide Bakshi shots.)

### Files / naming (official set, from Comfy-Org/MiniMax-H3)
- Diffusion: `minimax_h3_fl2va_pruned_int8_convrot.safetensors` 19.5 GB; ref2va equivalent 19.5 GB.
- Text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` 14.6 GB (Qwen3-VL 32B).
- VAEs: `minimax_h3_video_vae_fp16` 4.9 GB, `minimax_h3_audio_vae_fp32` 0.6 GB.
- Turbo LoRA (optional): `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16` 1.8 GB.
- Filename grammar: family `_` job (`fl2va`/`ref2va`) `_` `pruned` `_` precision. Precisions:
  bf16 (61.7 GB full / 37.5 pruned), int8_convrot (31.7 / 19.5), fp8_scaled (19.5, fallback),
  w6a8 (14.9, smallest official), nvfp4 (4-bit, text encoder default), awq (4-bit rounding method).
  `convrot` needs a recent ComfyUI whose startup log says `cu130`.
- Total official set ≈ 40 GB of model — bigger than 16 GB VRAM, runs by offloading (parts take turns);
  **the 32 GB of RAM is as much the tight spot as the card.**

### Settings (concrete starting values)
- Resolution: start 0.4 MP = **864×480**. Native is **0.98 MP (1344×768)**. Past 1344×768 you gain
  nothing (trained ~1 MP). **Skip the "1.0" setting — it lands just over the limit.**
- Duration: H3 is always 24 fps; **5 s = 124 frames** (matches our 17k+5 grid). Trained on roughly
  **5–15 s**; longer is untested territory. 5 s is the cheapest way to learn the other knobs.
- Steps: most gain by **step 16**; fine detail keeps improving to ~50. **Voices are weakest at 8
  steps, usable from 12 up.** Official default 20; drop to 12–16 for tests.
- Sampler `res_multistep` (official); `euler` = plain baseline. Scheduler `simple`; **for Ref2VA with
  lots of references, the official notes say `beta` or `normal` often does better.**
- Shift: `shift_video` 12, `shift_audio` 3 (built in; only visible with a ModelSamplingMiniMaxH3 node).
- **No CFG, no negative prompt** — H3 official workflows use a Basic Guider. A community CFG field at
  1.0 means off.
- Turbo LoRA: set steps to the number in the LoRA filename and match it to the model (fl2v turbo for
  fl2va, ref2v turbo for ref2va). **Same seed gives a different video with Turbo on vs off** — use it
  to test prompts, not to preview one exact take.
- Sage Attention: optional, official docs say ~2× speed; **if clip endings morph or on-screen text
  turns to garbage, turn it back off.**
- Change ONE knob at a time with the seed fixed.

### Errors (what they mean)
- Red boxes on open → missing custom nodes / older ComfyUI (H3 itself needs no custom nodes).
- "CUDA out of memory" → card full (lower MP / shorter clip / smaller files).
- **Dies after the last step finished → usually the video VAE running out while unpacking** (lower MP
  or shorter clip). Matches the VAE-unpack memory burst we've seen.
- Whole PC crawls → RAM full, Windows paging to disk.

---

## B. "The Power of Reference Videos for Believable Acting in Minimax" — 1x1umis
- https://www.reddit.com/r/StableDiffusion/comments/1x1umis/the_power_of_reference_videos_for_believable/
  (roychodraws, 607 upvotes, 121 comments)
- **This is the most FNI-relevant technique in the batch: use a video reference as a DELIVERY /
  performance reference, not a content reference.** Appearance comes from pictures; the source clip
  supplies cadence, pauses, pitch, emphasis, tone and facial manner; the source's own appearance,
  voice timbre, words, setting and framing are explicitly excluded.

The prompt pattern the author posted (his own words — "probably a bunch of phrases in here that do
nothing", but it worked):

```
<Subject 1> is the [character] whose entire appearance comes exclusively from <Picture 1>:
[appearance]. [She/He] speaks every line as an impression of the speaker in <Video 1>.

<Subject 2> is the [character] whose entire appearance comes exclusively from <Picture 2>:
[appearance]. [She/He] speaks every line as an impression of the speaker in <Video 1>.

<Video 1> is the delivery reference for both characters. They copy the speaker's cadence, pauses,
pitch changes, emphasis, tone and facial manner. Ignore the speaker's appearance, voice timbre,
words, setting and framing, and omit all text and watermarks.

<Video 1> (delivery style): fully_preserved - the speaker's cadence, pauses, pitch changes,
emphasis patterns, tone and facial manner are applied to both characters, while the speaker's
appearance, voice timbre, words, setting and on-screen text are excluded.

Both characters deliver every line ...
```

- Key points from the thread: "You have to prompt to be consistent with the actor you're trying to
  replicate." The author tried several phrasings; the phrases are not from the official guide — the
  text encoder "decides if it wants to understand you or ignore you" (4_gwai_lo). Prompt is all it
  took for the car scene — no movie-frame reference.
- Related thread: webitube — the same principle gives consistent worlds/shots; "there has to be a
  world source-of-truth."
- **FNI relevance:** our Track A (Rotoscope, 6-field REF2VA) uses the Bakshi video ref + Bakshi audio
  stem for 1:1 motion tracing. This gives a cleaner articulation of the *delivery* subset — we can
  keep the source's acting (cadence/emphasis/facial manner) while explicitly dropping its appearance,
  voice timbre and words. The `<Video 1> (delivery style): fully_preserved` line form is a drop-in
  shape for our `retention_analysis`. Two distinct uses of one video ref: (i) motion/choreography
  (our current Track A) and (ii) acting delivery (this technique) — we may want them as separate
  reference clips, or a single ref with a delivery-only retention line.
- Caveat from the thread: several commenters note the *audio* quality on these tests is still poor —
  consistent with the community-wide "H3 audio is the weak part" theme.

---

## C. "Mini max h3 models" — 1x1g4mu  (41 upvotes, 30 comments)
- https://www.reddit.com/r/StableDiffusion/comments/1x1g4mu/mini_max_h3_models/
- OP uses TaoMate 3-Step with the Eros model; asks for the fastest good-quality combo and any LoRA
  that reduces the plastic-skin effect. Community answers (directly relevant to our turbo-LoRA /
  audio-quality tension):

- **Base model: Singularity > Eros.** zakblues (top, +16): "Singularity for sure. I get much better
  results vs any Eros model." fa6637 agrees (singularity + LCM + people realism LoRA). ArtichokeFresh6793:
  "90% singularity with lightx2v 4-step turbo LoRA. two-sampling method is recommended."
- **Kijai's rank-reduced DMAD LoRA (zakblues, +16):** "great at around 5 steps+ and it fixes the shiny
  skin thing that most turbo LoRAs have"; the rank reduction also stops it overbaking faces; pairs with
  the new skin-detail LoRA for close-up portraits (BoorishCertainty).
- **Larry's V4 600-step LoRA (mellowanon):** runs at 8 steps, "the only turbo LoRA I've used that
  doesn't mess up the audio"; DMAD reportedly had bad audio when first released.
- Silveroxides test file: `silveroxides/MiniMax-H3_tests/minimax_h3_fl2v_turbo_silver_dareties_comfy_pruned_v1.safetensors`.
- Scheduler note (fa6637): **Beta / er-sde** with singularity + LCM.
- **FNI relevance:** reinforces the audio-degradation thread — turbo LoRAs vary a lot in whether they
  wreck the audio. Candidates to test against our 4-step LoRA: Larry's V4 600-step @ 8 steps
  (audio-safe), Kijai rank-reduced DMAD @ ~5 steps (skin/shiny-skin fix, audio uncertain), and the
  LightX2V 4-step at low strength. Singularity as the ref2va base.

---

## D. The cheat-sheet thread itself — 1x22omv comments
Light on technique: praise, an "it's still slop" critique of the LLM-written prose, and one open
question (Everwake8) — "do turbo LoRAs affect characters/action, or just speed?" (answer from the
guide: they soften detail and weaken voices; same seed ≠ same video with Turbo on/off). No new tips.

---

## E. "MiniMax H3: Seamless Long Videos, No Color Shift — SelfLift Dual Sampling" — r/comfyui 1wz3s0q
- https://www.reddit.com/r/comfyui/comments/1wz3s0q/minimax_h3_seamless_long_videos_no_color_shift/
  (wjc_5, 2026-10-06, 142 upvotes, 27 comments; flair "Tutorial"; 52 s demo video)
- **Directly our long-video stitching problem** (seam flicker + colour drift across chained
  segments). This is a refined motion-context chaining approach competing with obvpm/Motion-Context.
  The author calls it "SelfLift Dual Sampling"; three changes do the work:
  1. **Context mode = dual sampling: 4 low-res steps + 4 high-res steps, `lowres scale 0.65`
     (~1.5× upscale).** Fewer low-res steps + a smaller upscale ratio made the washed-out look
     AND the colour shift much less noticeable. (If a segment goes pale: lower the low-res step
     count and the upscale ratio first.)
  2. **Seam noise:** the reference frames right before the seam get **0.1 noise**, the last frame
     stays **clean** — this removed the flicker at the join.
  3. **Colour Transfer (`target_frame`):** match the new segment against the PREVIOUS segment's
     last frame, then apply the transform to the WHOLE new segment, so colour stays stable
     end-to-end. (His advice to another user: correct the colour shift at an intermediate stage so
     it doesn't keep degrading.)
- **Second stage uses a community-finetuned H3 latent upscaler, `h3_upscaler_lms_v0.1`** — visibly
  sharper than the stock one. `huggingface.co/Alissonerdx/Minimax-H3-ComfyUI/tree/main/latent_upscaler`
  (`h3_upscaler_lms_v0.1.safetensors` 0.69 GB; also an fp32 and a `..._sharpness_2000steps` build).
  **Not on the 5090** — added to `tools/download_5090_models.sh`.
- **New int8 VAE (ComfyUI 0.38.0+) roughly halves encode/decode time.** The 5090 already runs
  ComfyUI **0.38.0** and already has `minimax_h3_video_vae_int8_convrot` — so this lever is live.
- Acceleration LoRAs: he keeps the **4-step v1.2 and 8-step 768**; the recent **2-step LoRAs were
  "basically unusable"** in his tests (matches the wariness about Kijai pdmd 2-step).
- The context reference is a single switch — off, the workflow behaves like ordinary multi-reference
  generation.
- Links: online workflow `runninghub.ai/post/2105882473606447106?inviteCode=rh-v1495`;
  tutorial `youtu.be/NJwjjEv7NMc`.
- Comment caveats (unresolved): a static shot with a colourful background would be the honest demo;
  does it hold for a 30 s+ static-camera clip / a talking head (asked, not answered); several call
  the saturated synthetic-faces demo a weak test ("easy to claim no drift when the source has no
  natural skin tones or lighting").
- **FNI relevance:** concrete levers to A/B against our FL2VA frame-anchoring and the T0010
  motion-context chain — colour transfer at the seam, 0.1 noise on pre-seam reference frames,
  lowres scale 0.65 with 4/4 steps, and the `h3_upscaler_lms_v0.1` upscaler for the final pass.
  Our `tests/seam_probe.py` is the right instrument to judge it.

