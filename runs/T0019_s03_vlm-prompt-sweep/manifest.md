# T0019 — S03 FL2VA VLM-prompt sweep (s03-c02..c05), each vs its T0003 sibling

- Date: 2026-10-24
- Rig: VLM = mh370 4090 (LM Studio qwen3-vl-8b@q4), render = tombstone 5090.
- Method = T0018: VLM describes the chunk's actual first/last frames
  (cached in vlm_frames.json); deterministic assembler writes the FL2VA
  middle — technicolor style line, VLM first-frame anchor, ROSTER/consistent
  speaker strings bound to verbatim TSV dialogue (speaker + on/off-screen
  per the T0003 template), per-shot camera move, deferred-arrival ending
  anchored to the VLM last-frame read.
- One variable: node 138 prompt text. Each chunk reuses its T0003 graph
  verbatim (same bookend stills, same seed 1125345046553186, FL2VA weight,
  same per-chunk length, 20 steps).
- Chunks queued (5090 rebooted first -> fresh /history; prompt ids in queued.json):
  s03-c02 bc2e9cbf-6a0c-478a-abb0-b6af9f8c7576
  s03-c03 a14933b8-82e6-4b4f-86a4-24f9b0e933a8
  s03-c04 38de8901-6e95-4c67-ba7e-c35988187cf1
  s03-c05 e45e20e5-17ec-4eeb-abd2-a2b138c0e8f2
- Output prefixes: video/s03-cNN_T0019_t01 (T0003 siblings: s03-cNN_T0003_t01).
- Build: runs/build_t0019.py (--dry-run | --queue | --collect <prompt_id>).
- Scene scope: S03-c01 (T0018) + c02..c05 (T0019) = the whole S03
  throne-hall dialogue. For a full-scene watch: stitch the five VLM takes
  in story order (c01..c05) -> S03_T0019_stitched.mp4 and compare against
  T0003's s03_T0003_stitched.mp4. Source audio is overlaid per chunk at the
  compare step (T0008 audio-plan-A pattern).

## Per-chunk watch notes
- c02: Nekron seated, hands to face (VLM read), then cut to Juliana.
  Test the cross-cut: H3 must hold Nekron in shot 1 and the cut line.
- c03: both lines off-screen (Juliana + Nekron) over a seated white-haired
  figure — the prompt asserts the on-screen figure does NOT speak; watch it
  not invent lip sync on camera.
- c04: single-shot Nekron, "Perhaps." — the 5.17 s minimum-length case.
- c05: the envoys — VLM saw a pale woman with a scroll + three robed
  figures + the yellow-eyed envoy in the background. Multi-figure scene:
  watch cast count (no invented extras) and the ENVOY's yellow-eyes
  string holding.

## Verdict
(Alex, after watching the five takes / the stitched scene against T0003.)
