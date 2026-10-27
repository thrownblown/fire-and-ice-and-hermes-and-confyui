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

## [READ] "Can Qwen Image 2.1 replace multi-stage turnaround?" (1wmgbx9)
- https://www.reddit.com/r/StableDiffusion/comments/1wmgbx9/can_qwen_image_21_replace_multistage_turnaround/
- Digest: `docs/qwen21-turnaround-thread.md`
- Takeaway: Qwen Image 2.1 (7B DiT) holds 4-panel layout + identity coherence 44/44 in
  one T2I pass (~47s on a 3090) — but prompt-only fails framing (dwarfism, camera-distance
  drift, shin cropping). No prompt lever for camera distance/bounding boxes. Cheap wins:
  vertical 3:4/2:3 panels per quadrant, mandatory seed-hunting. Decouple medium emulation
  (style = post-pass, not in the sheet prompt). Directly relevant to FNI's identity-sheet
  work + the edit-model framing fix.

## [READ] Character-sheet 3-way — Krea2 vs Qwen 2.1 vs MiniMax H3 (video App5Rhnn-K0)
- https://www.youtube.com/watch?v=App5Rhnn-K0
- Digest: `docs/charsheet-krea2-qwen21-h3-comparison.md`
- Takeaway: Qwen 2.1 = best identity-holding (face closest to ref); MiniMax H3 = best
  sheet layout but face drifts every time; Krea 2 = mid, turnaround layout. Two cheap
  fixes: full-body reference (head-shots drift women into swimsuits — the Teegra failure)
  and check megapixels before debugging a stalled Qwen job. Sato Dive's H3 sheet workflow
  has style presets (realistic/anime/3D-Pixar/preserve-style).

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

## [READ] Seamless Vlog workflow — roycho87 (1x84uym)
- https://www.reddit.com/r/StableDiffusion/comments/1x84uym/make_perfect_seamless_vlog_videos_with_1_click/
- Digest: `docs/h3_clown_anchoring_overlap.md`
- Takeaway: Clown Anchoring = copy real next-shot latents into end of current shot's latent,
  hold with noise mask 0. No redraw flash (unlike Motion Context pinned frames which redraw
  brighter + 17-frame pulse). Overlap must be 17n+5 frames (5, 22, 39, 56...); default 39.
  Audio overlap is separate from video overlap (H3 audio on distinct timeline). GPL-3.0,
  ComfyUI custom nodes. For continuous content (talking head), not shot-cut content.

## [READ] Audio segmenter — roycho87 (1wtc1jo)
- https://www.reddit.com/r/StableDiffusion/comments/1wtc1jo/new_audio_segmenter_workflow_for_continuous_geiru/
- Digest: `docs/h3_clown_anchoring_overlap.md` §"Audio-side counterpart"
- Takeaway: Explicit 39-frame overlap formula for audio segmentation. Confirms "any 17n+5
  overlap works" and that audio/video overlaps are independent (different H3 timelines).
  Includes FL ChatterboxVC voice swap before splitting.
## [READ] ExactAudioLock — lock audio to exact frames before H3 generation
- https://www.reddit.com/r/StableDiffusion/comments/1wywoon/audio_outputs_differ_from_the_provided_audio_with/
- Repo: github.com/badids/ComfyUI-H3-ExactAudioLock
- Takeaway: build desired audio FIRST, position each line/sound at exact frame, input into
  H3 BEFORE generation. Full lock mode = H3 creates video to match that audio. Dialogue-only
  setting keeps spoken lines accurate while H3 produces ambience/foley/music. Multiple speakers,
  overlapping dialogue, per-event volume. Integrates with H3 Add Guide so audio + visual cues
  sync on same frame. NOT post-hoc audio paste. Directly applicable to FNI's
  dialogue-timeline.tsv.

## [READ] Most successful Ref2VA prompt structure (1x8scrg)
- https://www.reddit.com/r/StableDiffusion/comments/1x8scrg/most_successful_minimax_h3_referencetovideo/
- Takeaway: six-section REF2VA structure (subject_definitions / summary / retention_analysis /
  detailed_description / overall_soundscape / non_diegetic_music) — matches FNI's refrun.py
  grammar. CRITICAL: image ordering = clearest close-up face → image_1, body front → image_2,
  side/quarter → image_3. Trigger phrase: "The target is an [edited] version of [unchanged]".
  LOCAL H3 WEIGHTS: NEVER mention <Video N>, <Audio N>, or <Subject N> in detailed_description —
  define them in subject_definitions and retention_analysis only; use ONLY <Picture N> in
  detailed_description.

## [READ] Comfy Org invited H3 team — official guidance (1vj1czl)
- https://www.reddit.com/r/comfyui/comments/1vj1czl/comfy_org_invited_minimax_h3_team_to_talk_text/
- Takeaway: OFFICIAL — use quotation marks for exact dialogue lines ("...") to sync lip movement
  to audio. Keep prompts simple. Enhance with LLM. Megapixels node (0.4 MP ≈ 864×480). Define
  shots + duration (10s/5 shots = new shot every 2s). Up to 12 reference inputs. Kijai 4-to-8
  step LoRA. Quantized models. Keep ComfyUI updated (fine-grained H3 offloading).

## [READ] H3 first-day testing — ref_image_size=max, re-anchor character (1vemsal)
- https://www.reddit.com/r/comfyui/comments/1vemsal/minimax_h3_first_day_of_testing_mostly_just/
- Takeaway: ref_image_size = max (NOT match) for face/texture consistency across generations —
  slower but worth it. Frame sound as tangible events (impact, tearing, breathing) not vague
  mood — vague mood yields generic ambience. Explicitly re-anchor character in every clip.
  res_multistep + beta for reference-heavy prompts. RTX 5090, 96GB RAM baseline.

## [READ] Clip chaining — motion AND audio continuity (1vhppmv)
- https://www.reddit.com/r/StableDiffusion/comments/1vhppmv/clip_chaining_for_minimax_h3_motion_and_audio/
- Takeaway: Two 6s clips seamlessly combined — no crossfade, no editing tricks. Motion + audio
  flow continuously across junction. Repo: github.com/Niko80/ComfyUI-H3-Motion-Context (GPL-3.0).
  H3 lacks built-in consecutive-latent linking — this is the community solution. Competing
  approach to Clown Anchoring for the seam problem.

## [READ] H3 with heavy dialogue — audio quality update (1vrzu1o)
- https://www.reddit.com/r/StableDiffusion/comments/1vrzu1o/h3_minimax_with_heavy_dialogue/
- Takeaway: No quick fixes for dialogue. Turbo = subpar audio (general rule), BUT one report
  claims latest lightx2v turbo LoRA at 8 steps outperformed 32 steps for ref2v audio. Contradicts
  "more steps = better audio" — test against our setup. Use latest lightx2v LoRAs + latest Comfy.

## [READ] Minimax H3 Lipsync — segment + integrate approach (1wto9m7)
- https://www.reddit.com/r/StableDiffusion/comments/1wto9m7/minimax_h3_lipsync/
- Takeaway: Split audio into 10-15s segments, generate clips with audio, integrate using
  foxdit's minH3EDHTERLatent_v21 workflow. Official dialogue prompt guide exists. H3 has
  tendency to improvise — results significantly improved but not perfect.
- H3 latent upscale / second-pass threads (1w43syg; altoiddealer WF ships a latent upscale pass).
- H3 Spectrum speedup threads (xmarre ComfyUI-Spectrum-MiniMax-H3).
- H3 audio (dialogue/lip-sync) quality threads (1vj8nyp multi-speaker; 1vkh2mi any-language).
- Prompt-structure guides (1vnis23 cheat sheet; 1vfnby5 edited camera/sound guide).
- Gibberish-fix threads (1vxpbo1, 1viui81).
- Bakshi Fire & Ice or rotoscope-style LoRA threads, if any exist.

## [READ] Qwen-Image-Edit prompting cluster (10 threads, 2026-10-27)
- Playbook 1n1n81o · Edit-tips 1wlt9t9 · System prompt 1mudj7i · Drift 1xgpezp ·
  Design template 1wsgrh4 · Multi-ref 1x675fb · 2509 commands 1nuu6k3 ·
  Char-in-environment 1ovaew7 · Face consistency 1p11vaa · 2509 consistency 1o9r8e2
- Digest: `docs/qwen-edit-prompting-guides.md`
- Takeaway: identity-preservation clause AFTER the action instruction; address refs
  as "the person in image 1"; "same person" beats gendered nouns; "this background"
  when a ref supplies the setting; chain small edits; style-source-first; Consistence
  LoRA (civitai 1939453) for big edits; VL-caption the still to seed the video prompt.
  A/B test queued as T0026 against build_scenes.scene_prompt.
