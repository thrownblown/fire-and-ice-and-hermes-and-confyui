# T0004 — S03 FL2VA, motion-path prompts

- Date: 2026-09-29
- One variable vs T0003: the prompt's motion language. Same keyframes (chunk first/last
  source stills), same seed (1125345046553186), same weight, same node, same frame
  lengths, same dialogue assembly, same soundscape and music lines.
- What changed in integrated_multimodal_description:
  1. Every 'camera holds a static shot' became a slow single move (push in / pull out /
     truck right, small amplitude, slow speed).
  2. Each shot gained an observable-intermediate-change passage (breathing, gaze, hair,
     hand and head movement), grounded in the mid-shot stills local qwen3-vl-8b captioned
     for T0003. Those are visible things, not invented plot.
  3. The old 'the action resolves into the exact pose established by <Picture 2>' was
     replaced by arrival deferred to the last seconds, with the differences narrowing.
- Why: T0003 metrics showed the model reaching the last keyframe by 25-50% of the clip and
  then holding it; 4 of 5 chunks were more frozen than their ref2v counterparts. A static
  camera plus no intermediate states left the model nothing to do between the anchors.
- Question: does a written motion path wake up the middle of the clip without losing the
  keyframe anchoring that T0003 got right?
- Renders: video/<chunk>_T0004_t01 on the 5090. Compare against T0003 with the same
  frame metrics (frame-metrics.json in the T0003 run).

## Verdict
(Alex, after watching.)
