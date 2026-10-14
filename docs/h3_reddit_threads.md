# H3 Reddit Threads — index of relevant r/StableDiffusion reading

Purpose: a running index of community threads that inform the FNI H3 pipeline. Each entry:
link, why it matters, and the concrete takeaway. Per-thread digests go in their own
`docs/*_thread.md`; this is the map.

Status legend: [READ] digested in a separate doc · [TODO] known useful, not yet read.
Last full re-review: 2026-10-12 (`docs/h3_repull_2026-10-12.md`).

---

## [READ] "Minimax h3 veterans (share your wisdom)"
- https://www.reddit.com/r/StableDiffusion/comments/1x34suo/minimax_h3_veterans_share_your_wisdom/
- Digest: `docs/h3_veterans_thread.md` (re-pulled 2026-10-12 — 35 comments; see Re-pull section)
- Takeaway: seed instability → restart ComfyUI first; don't use the 4-step turbo LoRA at
  strength 1.0 for ref2video (full steps, or 0.4 strength); `max` ref_image_size for identity;
  say what you want not what you don't; state lip/hand behavior or H3 invents it. NEW 10-12:
  possible Comfy 0.35 adherence regression; gen-longer-than-ref makes H3 sing in the tail.

## [READ] "How much VRAM does H3 need? Less than you might think"
- https://www.reddit.com/r/StableDiffusion/comments/1vz2n7y/how_much_vram_does_h3_need_less_than_you_might/
- Digest: `docs/h3_repull_2026-10-12.md` §4. DORMANT (last comment 2026-08-30). Zironic's
  `H3 Memory Optimization` (fit long/hi-res video in VRAM) + `H3 Sparse Attention` (speed) nodes;
  50% attention budget suffices; int8 fine. Relevant to the 4090/5090 split.

## [READ] "Mini Video Editor / timeline node for H3 extend"
- https://www.reddit.com/r/StableDiffusion/comments/1wmj6xr/mini_video_editor_timeline_node_for_h3_extend/
- Digest: `docs/h3_repull_2026-10-12.md` §3. obvpm timeline workflow (extend/prepend/bridge/
  cut/loop/upscale) + YouTube tutorial. Refmods can be wired in and referenced by name; clip
  bridging is unreliable; heavy VRAM staging. Correct repo: github.com/chanon/comfyui-obvpm-timeline.

## [READ] Character consistency — sparkleriley "part 2" + portable identity
- https://www.reddit.com/r/StableDiffusion/comments/1wycwqr/minimax_h3_character_consistency_part_2/
- https://www.reddit.com/r/StableDiffusion/comments/1vyymwj/minimax_h3_portable_character_consistency_via/
- Digest: `docs/h3_repull_2026-10-12.md` §5–§6. Part 2 = source of the turbo-LoRA-deep-fries-
  audio rule. Portable identity = the `omnichar/ComfyUI-Omnichar` `.char` node (Comfy workflows
  for FLUX + H3), adjacent to our refmod workstream.

## [READ] "Minimax H3 Refmod Workflow" (1x4auud)
- https://www.reddit.com/r/StableDiffusion/comments/1x4auud/minimax_h3_refmod_workflow/
- Dainamo's two-workflow refmod setup. Mined 2026-10-12; JSONs saved to `explore/refmod-wf/`
  (MH3_Refmod_train_WF.json + MH3_Refmod_WF.json); full recipe folded into the fni-h3-pipeline skill.
- Takeaway: `H3RefModCreateFromFolder` (ComfyUI-MiniMaxH3Mod / Luisacaotica) bakes images +
  optional voice (ceiling 30s) into a `.refmod`; apply via `MiniMaxH3RefModsLoader`/`Apply`.
  Community stack: Singularity ref2va UNet, qwen3vl-32b nvfp4 text encoder, Spectrum forecast
  node (0.5 blend ≈ half gen time, not with turbo LoRA), taeh3 TAE preview.
- Re-pulled 2026-10-12 (new comments): 8192-token ceiling ⇒ ~8 images per refmod; refer to a
  refmod by NAME in the prompt (`<Subject 1> name ...`), multi-image refmod → `<Video x>`,
  audio refmod → `<Audio x>`; use the "Inspect" node to confirm tokens; a 6-min speech sample
  bakes a 1:1 voice clone (vs ~30s apply-time audio ref). Details in §2 of the repull doc.

## [READ] "H3 RefMods are great I highly advice trying it out" (1wclxbj)
- https://www.reddit.com/r/StableDiffusion/comments/1wclxbj/h3_refmods_are_great_i_highly_advice_trying_it/
- Digest: `docs/h3-refmods-thread.md`. The biggest RefMod thread (153 up, 89 comments).
- Takeaway: always `<Subject N>` (never `<Picture N>`/`<Background N>`), subjects defined in loader
  order; the real win is baked latents + freeing `<Picture>` slots (measured speed win only ~7%);
  background bleed from the refmod is the failure mode (fix: strength+retention = 1 plus the
  environment as First Image); voice-in-refmod is NOT proven. FranckyB fork adds audio/video refmods
  + a visual picker.

## [READ] RefMods / "refloras" (malcolmrey thread)
- Original workflow: https://huggingface.co/datasets/malcolmrey/workflows/blob/main/H3/workflow_minimaxh3_refmod.json
- Referenced in the FNI skill: RefMod nodes fed into the text encoder, per-subject tagging,
  audio voice-cloning refs. Concrete recipe now captured via the 1x4auud thread above.

## [READ] Shared 2026-10-12 — field guide, delivery refs, turbo-LoRA roundup
- Digest: `docs/h3_shared_threads_2026-10-12.md`
- **NimbleCloud13 H3 field guide** (post 1x22omv; repo nimblecloud13/ComfyUI-MiniMax-H3-Guide;
  local HTML `explore/h3-field-guide/`) — plain-English settings/file reference: 0.4 MP start,
  0.98 MP native (skip "1.0"), 5 s = 124 frames, voices weakest at 8 steps (usable 12+),
  `res_multistep`/`simple` (beta/normal for heavy Ref2VA), no CFG, dies-after-last-step = video VAE.
- **Delivery-reference technique** (1x1umis, roychodraws) — use a video ref for ACTING (cadence,
  pauses, pitch, emphasis, tone, facial manner) while appearance comes from pictures and the
  source's appearance/voice/words/setting are excluded. Directly applicable to Track A.
- **Turbo-LoRA / base-model roundup** (1x1g4mu) — Singularity > Eros; Kijai rank-reduced DMAD fixes
  shiny skin at ~5 steps; Larry's V4 600-step @ 8 steps is the audio-safe turbo LoRA.
- **Seamless long videos / no colour shift** (r/comfyui 1wz3s0q, wjc_5 "SelfLift Dual Sampling") —
  dual sampling (4 low-res + 4 high-res steps @ lowres scale 0.65), 0.1 noise on pre-seam ref frames
  with a clean last frame, and Color Transfer against the previous segment's last frame; plus the
  `h3_upscaler_lms_v0.1` latent upscaler. Levers for our seam/colour-drift problem.

## [READ] Peer projects — Lumibelle/SparkleRiley + Frameforge (2026-10-12)
- Digest: `docs/h3-peers-2026-10-12.md`. Official MiniMax prompt guides vendored to `docs/h3-official/`.
- **Lumibelle** (github.com/radiatingreverberations/lumibelle; project `sparkleriley`, CC0) — a full
  H3 film studio whose project data model maps ~1:1 onto FNI. Its 2026-09-11 acceleration benchmark
  (RTX 4000 Ada, base pruned W4A8 ref2va, 141 frames) is the best measured comparison we have:
  **Larry v4 step600 EMA @ 6 steps won** (31–34 % faster than Standard, judged Good on motion);
  Turbo 4/8-step and Spectrum gave "weird interiors"; PDD distorted dialogue; Sol-Attn and
  FirstBlockCache failed. Also: an exact stock-node motion-extension contract (39/22/5-frame
  contexts, 17k+5, max 362 @ 24 fps), a 243-frame character-orbit reel plan, and the HyperFlow
  8-step frozen recipe.
- **Frameforge** (github.com/spacesimeco-hue/Chain-Motion-AI-Video-Editor; reddit 1x4fq9m) — single-
  track generative timeline, latent motion continuation at context lengths 22/39/56 (same grid as
  our `core/h3_chain.py`), Speech Studio (LTX 2.3 voice ref), and **Set Studio** (3D staging →
  rendered reference images = a master-plate generator route).

## Backlog — search for / not yet scraped (see repull doc §"Threads NOT yet in the index")
- H3 latent upscale / second-pass threads (1w43syg; altoiddealer WF ships a latent upscale pass).
- H3 Spectrum speedup threads (xmarre ComfyUI-Spectrum-MiniMax-H3).
- H3 audio (dialogue/lip-sync) quality threads (1vj8nyp multi-speaker; 1vkh2mi any-language).
- Prompt-structure guides (1vnis23 cheat sheet; 1vfnby5 edited camera/sound guide).
- Gibberish-fix threads (1vxpbo1, 1viui81).
- Bakshi Fire & Ice or rotoscope-style LoRA threads, if any exist.
