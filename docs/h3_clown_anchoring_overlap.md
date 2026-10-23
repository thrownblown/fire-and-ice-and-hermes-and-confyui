# H3 Clown Anchoring & the 39-Frame Overlap — durable summary

Source: roycho87's GitHub repos + Reddit thread
`r/StableDiffusion 1x84uym — "Make Perfect Seamless Vlog Videos with 1 Click"`
and the audio-segmenter follow-up `r/StableDiffusion 1wtc1jo`.
Repos: `h3_clown_anchoring`, `comfyui-load-audio-batch-from-dir`,
`minimax_continuous_audio_splitter`, `seamless_video_combiner`,
`Seamless_vlog_workflow`. All GPL-3.0, ComfyUI custom nodes / workflows.

---

## What it is

A technique for making MiniMax H3 video clips join without a flash at the seam.
Instead of guide-based anchoring (Motion Context pinned frames, native H3 Add Guide),
which shows the model the previous frames as conditioning and **redraws its own copy**
— coming out brighter with a 17-frame pulse — clown anchoring **copies the real saved
latents** from the next shot into the end of the current shot's starting latent and
holds them with a noise mask (0). The sampler keeps those frames as-is, so they decode
as the originals. No redraw, no flash.

The technique comes from roycho87's work on "pull forward." It extracts latent
information from the preceding video, unpacks it, and repositions it at the end of
the current video with a mask — generating contextual motion for the conclusion of
the current video.

## The nodes

**Clown Anchoring** (`latent/H3` after install):
- Inputs: `latent` (starting AV latent), `tail_frames` (overlap, default 39),
  `drop_17_frames` (holds one 17-frame block less — with 39, holds 22 instead),
  `next_shot` (optional, next shot's saved latent from H3 Motion Context Load Latent).
- What it does: copies `tail_frames` from the end of this shot's latent from the
  next shot's first `tail_frames`. With 243-frame clips and `tail_frames=39`, this
  shot's frames 204–242 are held as the next shot's frames 0–38.
- Existing noise masks (e.g. audio masks) are preserved.
- Console reports what was held: `[Clown Anchoring] held latents 60..71 = frames 204..242 <- next shot's frames 0..38`

**H3 Repack AV Latent** (list → packed):
- Motion Context Load Latent returns a plain `[video, audio]` list. VAE Decode,
  VAE Decode Audio, and LTXV Separate AV Latent need the packed form. This node
  converts between them.

## Why 39 frames

**39 = 5 + 17×2** — it's of the form `5+17k`. H3's frame grid is `17k+5` at 24fps;
every 5 latents make a 17-frame block, blocks start at frames 0, 17, 34...

A latent only reads correctly at the same position in its block. So clown anchoring
only copies latents where source and target positions line up.

With clip lengths and overlaps both of the form `5+17k` (e.g. 243 and 39), the
overlap always starts on a block boundary, so the **whole overlap can be held**.
Other overlaps are rounded down to the nearest boundary-aligned value (the console
says so).

**Any `17n+5` overlap works** — 5, 22, 39, 56, 73, 90... The author's default is
39. From the audio-segmenter thread (1wtc1jo): "H3 handles audio processing on a
distinct timeline compared to video blocks. To ensure the overlap functions correctly
and remains synchronized, you actually require 39 frames of overlap... Any
configuration within 17n+5 frames of overlap will work."

## Audio-side counterpart

The `minimax_continuous_audio_splitter` workflow splits a long audio into segments
with the same overlap. Formula (from the thread): `ceil(max(?, round(A * B - C) / 17))`
where A = duration seconds, B = fps, C = overlap frames. First segment starts at 0,
ends at f. Next segment starts at f − C (fsub1), ends at fsub1 + f. Next starts at
fsub1 + f − C (fsub2), ends at fsub2 + f. Repeats.

The audio splitter includes FL ChatterboxVC for voice modification before splitting.

`comfyui-load-audio-batch-from-dir` loads the split audio files back in order,
joining them end-to-end (converted to first file's sample rate/channel count).

## Install

1. Clone or download `h3_clown_anchoring` into `ComfyUI/custom_nodes/`.
2. Clone or download `comfyui-load-audio-batch-from-dir` into `ComfyUI/custom_nodes/`.
3. Restart ComfyUI.
4. Requires ComfyUI with MiniMax H3 support (`comfy.nested_tensor`).

## Limits

- Both clips must share the same model, resolution, and latent layout.
- The sampler must honour noise masks on the video latent (works with
  SamplerCustomAdvanced in the author's tests).
- The overlap frames are copies of the next shot. When joining, keep the overlap
  once: trim the end of this shot OR the start of the next.
- **This fixes the join, not long-chain drift.** Chaining many continuations still
  slowly darkens and softens the picture, same as Motion Context.

## Relevance to FNI

**Mathematically:** 39-frame overlap is 100% compatible with all 494 FNI chunks
(every chunk length is `5+17k`, so `L − 39` is always divisible by 17). The overlap
always lands on a block boundary — no rounding, no partial copies.

**Structurally:** FNI chunks are rendered independently with FL2VA + source-still
bookends (fullrun.py). Clown anchoring requires *continuation* rendering (chunk N+1
as a continuation of chunk N, fed with chunk N's end latent via Motion Context). These
are incompatible models. Switching would be a pipeline rewrite.

**Content-wise:** FNI chunk boundaries always fall on shot boundaries (verified:
1308 shots, each in exactly one chunk). At a join, you go from shot X's last frame
to shot Y's first frame — different content. Clown anchoring's seamless join is for
continuous content (talking head across segments). For shot-to-shot cuts, holding
the overlap just repeats shot X's end, which is what a normal edit already looks like.

**Audio-wise:** FNI audio is shot-aligned (dialogue-timeline.tsv). A 39-frame audio
overlap would blend two different dialogue streams across a shot cut. The seamless
vlog workflow's audio overlap is for continuous talking-head content, not shot-cut
content. FNI audio continuity is handled by the shot timeline, not by overlap.

**The medium-register angle:** The direction doc's Test 1 (S05-c01) showed FL2VA +
source stills is "structurally incapable of changing the medium register" (mean pixel
diff 2.2% from source still). Continuation rendering with clown anchoring *might*
escape the source-still anchor — but that's a separate hypothesis from whether
clown anchoring fixes joins, and it hasn't been tested on FNI material.

## Verdict

39-frame overlap is the right number for H3 chaining in the abstract. For FNI's
current FL2VA pipeline it doesn't apply (different rendering model + shot-cut content).
If FNI moves to continuation rendering, clown anchoring + 39-frame overlap is the
correct join technique to adopt. The audio overlap side does not apply to FNI (shot-
aligned audio, not continuous).

## Files

- Durable summary: this file (`docs/h3_clown_anchoring_overlap.md`)
- Thread index: `docs/h3_reddit_threads.md`
- Reddit thread: https://www.reddit.com/r/StableDiffusion/comments/1x84uym/
- Audio segmenter thread (39-frame formula): https://www.reddit.com/r/StableDiffusion/comments/1wtc1jo/
- Clip chaining thread (competing approach): https://www.reddit.com/r/StableDiffusion/comments/1vhppmv/
- Seamless long videos / no colour shift thread: https://www.reddit.com/r/comfyui/comments/1wz3s0q/
- Repos: github.com/roycho87/{h3_clown_anchoring,comfyui-load-audio-batch-from-dir,
  minimax_continuous_audio_splitter,seamless_video_combiner,Seamless_vlog_workflow}
