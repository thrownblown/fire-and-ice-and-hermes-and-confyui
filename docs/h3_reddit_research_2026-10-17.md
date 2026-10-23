# H3 Reddit research batch — 2026-10-17

New threads found and digested. Focus: audio/dialogue, prompt structure, character
consistency, continuation/seaming, and official guidance. Each entry: link, concrete
takeaway, FNI relevance.

---

## Audio / Dialogue / Lip-Sync

### ExactAudioLock — position audio at exact frames BEFORE generation
- https://www.reddit.com/r/StableDiffusion/comments/1wywoon/audio_outputs_differ_from_the_provided_audio_with/
- Repo: github.com/badids/ComfyUI-H3-ExactAudioLock
- Core technique: build the desired audio FIRST, position each line/sound at the exact
  frame, then input that audio into H3 **before** generation. In full lock mode, H3 creates
  the video to match that specific audio — not trying to replicate or estimate it.
- Dialogue-only setting: keeps spoken lines accurate while H3 produces other scene audio
  (ambience, foley, music). Multiple speakers, overlapping dialogue, precise timing,
  per-event volume adjustments.
- Integrates with H3 Add Guide so audio events AND visual cues sync on the same frame.
- NOT "paste audio back afterward" — audio is a core part of what H3 is generating.
- **FNI relevance:** directly applicable to `script/dialogue-timeline.tsv`. We have exact
  lines with start/end PTS. ExactAudioLock would let us lock each line to its frame and
  have H3 generate video to match — solving the dialogue sync problem at the source instead
  of fixing it in post. This is the highest-impact audio finding for FNI.

### Turbo LoRA at 8 steps can outperform 32 steps for ref2v audio
- https://www.reddit.com/r/StableDiffusion/comments/1vrzu1o/h3_minimax_with_heavy_dialogue/
- Claim: turbo LORA at 8 steps performed better than 32 steps for ref2v audio (one comment,
  exclusive ref2v use, latest lightx2v loras + latest Comfy).
- Counterpoint: another thread says turbo = subpar audio, upscalers mess up lip sync, lower
  steps hurt both. No consensus — but the 8-step claim is new and contradicts the "more steps
  = better audio" heuristic. Test against our current setup.
- **FNI relevance:** updates the turbo-LoRA guidance. We should test Larry V4 600-step @ 8
  steps (audio-safe per earlier research) against the latest lightx2v at 8 steps for ref2v
  audio quality.

### Official dialogue prompt guidance exists
- https://www.reddit.com/r/StableDiffusion/comments/1wto9m7/minimax_h3_lipsync/
- "An official guide exists regarding prompts for dialogue." (comment)
- Also: split song into 10-15s segments, generate individual clips with audio files, then
  integrate using foxdit's workflow (minH3EDHTERLatent_v21).
- **FNI relevance:** confirm the official dialogue prompt guide exists and get it. The
  segment-and-integrate approach matches FNI's chunk structure (15s cap).

### Frame sound as tangible events, not vague mood
- https://www.reddit.com/r/comfyui/comments/1vemsal/minimax_h3_first_day_of_testing_mostly_just/
- RTX 5090, 96GB RAM. ref_image_size = max (not match) for face/texture consistency across
  generations — slower but worth it.
- "Frame sound as tangible events with specific timing — like impact, tearing, or breathing —
  rather than using vague mood descriptors. The latter tends to yield generic ambience."
- "Explicitly re-anchor the character in every clip instead of assuming continuity."
- Use res_multistep + beta over simple for reference-heavy prompts.
- **FNI relevance:** the "frame sound as tangible events" tip directly applies to FNI's
  overall_soundscape and non_diegetic_music prompts. "Explicitly re-anchor character in every
  clip" is the character consistency rule. ref_image_size = max is the setting for face
  consistency — directly relevant to our wide Bakshi shots where H3 loses faces.

---

## Prompt Structure

### Six-section REF2VA structure — tags in the RIGHT sections
- https://www.reddit.com/r/StableDiffusion/comments/1x8scrg/most_successful_minimax_h3_referencetovideo/
- Structure: subject_definitions / summary / retention_analysis / detailed_description /
  overall_soundscape / non_diegetic_music
- Tags: <Subject N>, <Picture N>, <Video N>, <Audio N>
- CRITICAL: connect clearest close-up face to image_1, body front to image_2, side/quarter
  to ref_image_3.
- Trigger phrase: "The target is an [edited] version of [unchanged]" — transitions model into
  frame-by-frame video editing mode.
- LOCAL H3 WEIGHTS PECULIAR BEHAVIOR: avoid mentioning <Video N>, <Audio N>, or <Subject N>
  in detailed_description. Always define images within subject_definitions and
  retention_analysis, and use ONLY <Picture N> in detailed_description.
- **FNI relevance:** this is exactly FNI's refrun.py grammar (6-field). The "don't mention
  <Video>/<Audio>/<Subject> in detailed_description" rule is new and directly applicable to
  the prompt crafter. The image ordering tip (face→image_1, body→image_2, side→image_3) is
  actionable for our character sheet workflow.

### H3 prompting cheat sheet — scene/subject/beat/dialogue/audio structure
- https://www.reddit.com/r/StableDiffusion/comments/1vnis23/minimax_h3_prompting_cheat_sheet_this_structure/
- Format: Subject Action + Environment + Camera Timing + Audio
- Template: Scene / Subject / 0–Xs / Xs–Ys / [Dialogue Speaker]: "Exact line" / Amb audio /
  SFX / Music / Visual style
- Treat audio elements as an additional layer of the prompt.
- When providing refs, don't just upload — state what each reference controls.
- **FNI relevance:** the beat-by-beat structure (0–Xs, Xs–Ys) matches FNI's ledger-driven
  motion rule. The dialogue-in-quotes pattern matches the official guidance. Reinforces the
  prompt crafter's direction.

### Qwen 3.8 writes better H3 prompts than 3.6
- https://www.reddit.com/r/StableDiffusion/comments/1vojrzv/qwen_38_is_out_and_it_writes_awesome_minimax/
- Qwen 3.8 outperforms 3.6 with same system prompt.
- Principles: concrete observable details (subject, wardrobe, prop, setting, action, camera,
  lighting, mood, ambience, sound). Reference tags only when available. State exactly what each
  reference controls (identity, face, hairstyle, body proportions, wardrobe, accessory, prop,
  environment, audio performance). Explicitly describe ambience, Foley, impacts, wind, cloth
  movement, crowd sound, music.
- Structure: Visual style / Scene overview / Storyboard / Camera / Audio / Consistency.
- **FNI relevance:** if FNI uses an LLM for prompt crafting, Qwen 3.8 is the model to use.
  The "state exactly what each reference controls" rule is the delivery-reference technique
  from 1x1umis, now confirmed as a general prompt principle.

### Official H3 team talk — quotation marks for dialogue
- https://www.reddit.com/r/comfyui/comments/1vj1czl/comfy_org_invited_minimax_h3_team_to_talk_text/
- Comfy Rob (Comfy Org): "Use Quotation Marks for Dialogue — when incorporating reference audio
  and requiring a character to speak, place exact dialogue in quotation marks within text prompt.
  This allows the model to synchronize the character's lip movements with the audio accurately."
- Keep It Simple — no complex prompt engineering terminology.
- Enhance Prompts with an LLM — Comfy Rob uses an LLM node to transform basic ideas into
  detailed step-by-step prompts.
- Megapixels node instead of width/height (0.4 MP ≈ 864×480).
- Define shots and duration: "10-second video with 5 shots" → model produces a new shot every
  2 seconds.
- Up to 12 reference inputs for temporal/spatial coherence.
- **FNI relevance:** quotation marks for dialogue is the official H3 team guidance — directly
  applicable to FNI's dialogue-timeline.tsv lines. The "define shots and duration" feature is
  interesting for FNI's chunk structure. The LLM-prompt-enhancement approach validates the
  prompt crafter direction.

---

## Continuation / Seaming / Long Video

### SelfLift dual sampling — 6 low-res + 2 high-res, single guide
- https://www.reddit.com/r/comfyui/comments/1wkmopn/minimax_h3_ultraflexible_directors_console/
- SelfLift: 6 low-res steps + 2 high-res steps (shifted from 4+4 and 2+6). Single high-res
  guide resampled for low-res pass — better alignment in continuations, minimizes small seam
  offsets. Skipping second pass eliminates seam issues but loses speed.
- **FNI relevance:** continuation alignment improvement. If FNI moves to continuation rendering
  (see clown anchoring analysis), SelfLift is the sampling approach to use. Complements the
  SelfLift Dual Sampling thread (1wz3s0q) already in the index.

### Endless H3 with latent save/load + stitching
- https://www.reddit.com/r/comfyui/comments/1w5e6pl/endless_minimax_h3_with_endless_lipsync_v10/
- Save/load latents from every generation. Stitch all (or selected) clips whenever a complete
  video is desired. Supports FL2VA and Ref2VA. Stitch Clips + Save Video = concatenate
  h3_context folder clips.
- **FNI relevance:** the latent save/load + deferred stitch approach is an alternative to
  real-time stitching. For FNI's 494 chunks, saving all latents and stitching at the end is
  a viable workflow — but requires disk space for 494 latent files.

### Prompt Queue + Batch Minimax — prevents long-chain deterioration
- https://www.reddit.com/r/comfyui/comments/1w4m8r4/a_quick_minimax_h3_news_roundup_1st_september_2026/
- MiniMax H3 Prompt Queue: store multiple motion prompts in one node, queue in order.
- Batch Minimax: one ref image + one video ref + prompt file, process all in batch.
- "Prevents gradual deterioration of scenes or characters during generation of longer videos
  (>30 seconds) using Minimax clip-chainers."
- **FNI relevance:** directly addresses the long-chain drift problem. FNI's 494 chunks
  (many scenes >30s) would benefit from a prompt-queue approach that resets character identity
  per chunk.

### Clip chaining with motion AND audio continuity
- https://www.reddit.com/r/StableDiffusion/comments/1vhppmv/clip_chaining_for_minimax_h3_motion_and_audio/
- Two 6-second clips seamlessly combined — no crossfade, no editing tricks. Motion and audio
  flow continuously across the junction.
- Repo: github.com/Niko80/ComfyUI-H3-Motion-Context (GPL-3.0). H3 lacks built-in capability
  for linking consecutive latent frames directly to the start — this is the community solution.
- **FNI relevance:** competing approach to clown anchoring for the seam problem. Worth comparing
  Motion Context vs Clown Anchoring for FNI's use case. Already partially known (mentioned in
  shared threads doc) but not in the thread index — should be added.

---

## Character Consistency / Reference

### ref_image_size = max, not match, for face consistency
- https://www.reddit.com/r/comfyui/comments/1vemsal/minimax_h3_first_day_of_testing_mostly_just/
- "Use max for ref_image_size instead of match when you need faces or textures to remain
  consistent across generations. It's slower, but worth it."
- **FNI relevance:** directly contradicts any "use match" guidance. For FNI's character shots
  where H3 loses faces in wide frames, max is the setting. This should be the default for
  character-consistency renders.

### Re-anchor character in every clip
- Same thread (1vemsal): "Explicitly re-anchor the character in every clip instead of assuming
  continuity."
- **FNI relevance:** the character consistency rule for FNI's chunk pipeline. Each chunk should
  explicitly re-establish the character from Picture 1, not assume the previous chunk's output
  carries identity.

### Detailers for faces/text at low res
- https://www.reddit.com/r/comfyui/comments/1w2wcnh/collection_of_minimax_h3_workflows/
- Qwen 3 VL 4B prompt generators for T2VA, I2VA, Ref2VA.
- Detailers: crop, resample, reintegrate at full res, mask-agnostic (SAM, YOLO). Work with refs,
  denoise 0.4–0.75, diminishing returns after 6 steps. Can work with as few as 3 steps.
- **FNI relevance:** detailer approach for fixing faces/text in H3 output. Relevant to the
  still-gen pipeline and any post-H3 face fix. Qwen 3 VL 4B prompt generators could feed the
  prompt crafter.

---

## Open questions raised

1. **ExactAudioLock availability** — is the badids/ComfyUI-H3-ExactAudioLock node compatible
   with FNI's ComfyUI setup? Does it work with Ref2VA (FNI's grammar) or only FL2VA?
2. **Turbo LoRA audio at 8 steps** — test Larry V4 600-step @ 8 vs latest lightx2v @ 8 for
   ref2v audio. Contradicts earlier "more steps = better audio" finding.
3. **Official dialogue prompt guide** — locate and read it. The 1wto9m7 thread says it exists.
4. **Clip chaining (1vhppmv) vs Clown Anchoring (1x84uym)** — which is better for FNI's
   shot-cut content? Both solve the seam problem differently.
5. **Prompt Queue for long-chain drift** — does the deterioration-prevention claim hold for
   FNI's 494-chunk structure? Test on one long scene.
6. **Qwen 3.8 for prompt crafting** — FNI currently uses which model for prompt enhancement?
   If 3.6 or earlier, upgrade to 3.8.
