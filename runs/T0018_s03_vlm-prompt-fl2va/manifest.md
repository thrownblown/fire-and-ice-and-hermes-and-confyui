# T0018 — S03 FL2VA, VLM-authored prompt (vs T0003 template)

- Date: 2026-10-24
- Rig: VLM = mh370 4090 (LM Studio qwen3-vl-8b@q4), render = tombstone 5090.
- One variable: node 138 prompt text. Everything else is T0003's exact
  s03-c01 graph, reused verbatim — same two bookend stills
  (s03-c01_first.jpg / s03-c01_last.jpg, both = source shot 00067), same
  seed 1125345046553186 (RandomNoise node 129), same FL2VA weight
  h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors, same 20 steps,
  same 5.88 s / 345-frame length (PrimitiveFloat 5.875 -> 17k+5 snap).
- Chunk: S03-c01 (single source shot 00067, Juliana at the Ice Peak throne
  hall, lines L023 + L024, both her, conf HIGH). Same framing at both
  anchors — the dead-middle risk case, so a good VLM middle should show the
  biggest delta vs the template.
- Build: runs/build_t0018.py. VLM cache in vlm_frames.json (rebuild is free).
- Reference take (prompt-only control): T0003/s03-c01_T0003_t01 (copied into
  this run as ref_T0003_s03-c01.*).
- Output prefix: video/s03-c01_T0018_t01.
- Prompt id: afaa94ce-112b-4329-95f4-e83917c9ae1c (queued 2026-10-24).
- Audio: FL2VA generates its own; source master audio is overlaid at stitch
  (T0008 audio-plan-A pattern), so the heard audio is the source's either way.

## The prompt diff (what changed vs T0003)
T0003 (template): old "2D-animated rotoscope painted animation in the style of
a 1983 fantasy film" style line; "the camera holds a static medium three-quarter
shot"; "The action resolves into the exact pose, framing, and composition
established by <Picture 2>: <VLM last-frame caption>".

T0018 (VLM-authored middle): current technicolor 80s sword-and-sandals style
line (fullrun.style_line, the live direction); VLM description of the ACTUAL
first frame (profile, right side, head high, gaze forward) anchoring <Picture
1>; the ROSTER/consistent speaker string + verbatim dialogue; observable
intermediate change (shifted gaze, tilt of the head, settle of the gown) with
deferred arrival — "Only in the last seconds ... slows and stops, and the
figure comes to rest in ... : <VLM last-frame caption (centered, head tilted
upward)>". The VLM read of the two frames is the real in-shot micro-motion of
source shot 00067, so the middle is grounded in the material, not a generic
standing gesture.

## Watch for (one variable per test -> the verdict below is the delta)
- Does the VLM frame-anchored description keep Juliana where T0003's template
  had her (or better)? Same seed, so a movement difference is the prompt,
  not the noise draw.
- Dead middle: T0003's "resolves into the exact pose" tends to land on
  Picture 2 early then hold. T0018's deferred-arrival middle should move
  (gaze/head/gown) through the clip and settle only at the end.
- Consistent character string: does the ROSTER-based speaker description hold
  her identity the same way the template's richer per-shot people row did?
- Structure (frame_metrics): anchor check (frame 0 ~ Picture 1, last ~
  Picture 2), position profile (no early L L L), frozen fraction.

## Verdict
( Alex, after watching T0018 vs T0003 side by side. )
