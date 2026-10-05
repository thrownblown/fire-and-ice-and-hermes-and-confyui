# H3 ref2v prompt template

Settings baseline is the 2026-09-25 graph:
`corpus/2_low_mm_20260925_091204_00001-audio.json`.

The clip that graph produced looked right. Only the dialogue was a joke
for a work audience. Keep the subject lines, the picture lines, and the
style of the descriptions. Drop the spoken lines.

## Baseline graph (that file)

- Node: MiniMaxH3ReferenceToVideo
- The prompt lives in a separate string node, wired into `prompt`. The
  node's own prompt widget was empty.
- Model loaded on that run: h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors
  That is the first-last-frame weight. For identity chunks prefer
  h3/minimax_h3_ref2va_pruned_int8_convrot.safetensors.
- CLIP: qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
- Video VAE: minimax_h3_video_vae_int8_convrot.safetensors
- Audio VAE: minimax_h3_audio_vae_fp32.safetensors
- Size: 1344x768. ref_image_size: match. length: 124 frames (5.17s at 24fps).
- Slots wired: ref_image_0 through ref_image_4 (5 images; slot 5 and 6 empty),
  plus two ref videos and their audio. Six images is the cap, not the requirement.
- Low preview combine: CRF 19, 24 fps, save_metadata true.
- Upscale path, separate file: sigmas 0.9035, 0.8000, 0.6316, 0.3158, 0.0000,
  then RIFE to 48 fps, CRF 16.
- Sigma shift: video 6, audio 3.

LoRAs on that run were for a different clip (two on, eight off). Do not
copy those strengths into story chunks.

## Weights on the 5090

`/home/thrownblown/comfyvenv/ComfyUI/models/diffusion_models/h3/`:

- minimax_h3_ref2va_pruned_int8_convrot.safetensors — ref2v, use this for story chunks
- minimax_h3_ref2va_pruned_w4a8_mixed.safetensors — same role, tighter quant, untested
- MiniMax-H3-Pruned-Ref-Delta-Fused-r1024-comfy-int8-convrot.safetensors — fused ref delta, untested
- minimax_h3_fl2va_pruned_int8_convrot.safetensors — first-last-frame, what that graph loaded
- minimax_h3_fl2va_pruned_w4a8_mixed.safetensors — first-last-frame, tighter quant
- 10Eros_Max_h3_TURBO-hybrid_beta4_int8_convrot.safetensors — turbo hybrid, not for story chunks
- minimax_h3_fastvideo_vsa_datafree_1300step_4step_int8_convrot.safetensors — 4-step distill, not for story chunks

Do not point a ref2v graph at an fl2va file, or the reverse.

## Reference slots

Up to 6 images, wired as Picture 1..N. That graph used 5. Each picture line
says what the still is for and whether it is a frame anchor or a weak
reference. Name the files in the graph, not in the prompt. The prompt
refers to <Picture N> only.

## Prompt shape

The shape from that graph, with the junk removed. Fill the brackets.
Physical traits, not names. A name may appear inside a spoken line only.

    subject_definitions:
    <Subject 1>: the woman with long black hair and a purple two-piece, gold earrings and necklace. Seen in <Picture 1>, <Picture 3>.
    <Subject 2>: the blond man, muscular, brown belt with a gold buckle, bone necklace. Seen in <Picture 2>, <Picture 3>.

    <Picture 1>: [what this still shows, which shot it anchors, and what it must NOT import].
    <Picture 2>: ...

    summary: reference generation, [N] shots, [audio reused or not].

    retention_analysis:
    <Subject 1> (appears in [Shot 1], [Shot 2]): attribute_transfer — retains [3-5 traits: hair, clothing, one prop].
    <Picture 1>: fully_preserved | weak_reference — [why].

    detailed_description: rotoscope painted animation, [place], [time of day].
    [Shot 1] [camera, one move]. [who does what]. [spoken line if any: [English] "..."].
    [Shot 2] At 00:02.000, [camera]. [action].
    overall_soundscape: [diegetic only: wind, fire, footsteps, voices].

## Rules

- Repeat the same 3-5 traits in retention_analysis that you listed on the subject.
- Every picture line states a negative: what action or pose must not leak in.
- 2 or 3 shots. Timecodes are absolute from 00:00.000 and must fit the length.
- One camera move per shot. Do not stack moves.
- Dialogue is one short line with a language tag. H3 will not honor a paragraph.
  Do not repeat a line the ASR already attached to the previous shot.
- Style line says rotoscope / painted animation unless you are deliberately
  leaving the film look. The baseline graph said live-action. That was wrong
  for these chunks.
- For story chunks, forced stems win over the soundscape block.

## What not to copy

- The spoken lines in that graph. They were a joke for a work audience. The picture, the subjects, and the camera notes were fine.
