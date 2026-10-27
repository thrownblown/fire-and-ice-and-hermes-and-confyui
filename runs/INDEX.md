# Test runs

| id | scope | method | verdict |
|---|---|---|---|
| T0001 | S03 | ref2v, original stills | decent — Alex, 2026-09-27 |
| T0002 | S03 | ref2v, same refs and seed, split at action beats | pretty good — Alex, 2026-09-28 |
| T0003 | S03 | fl2va (first/last source stills), same chunks and seed as T0002 | (Alex, after watching) |
| T0004 | S03 | fl2va motion-path variant (source frame deltas), 2 takes | (Alex, after watching) |
| T0005 | S03 | fl2va action variant | (Alex, after watching) |
| T0008 | S03 | original master audio over the T0001 video (audio plan A baseline) | audition pending |
| T0009 | S02 | continuity-packed segments (SSIM chains/setups) vs chronological | renders done — compare S02_continuity_audioA vs S02_chronological_audioA |
| T0011 | S06 | setup-ref2va baseline: chronological chunk S06-c01 (3 shots) | (Alex, after watching) |
| T0012 | S06 | setup-ref2va stitched-video: setup S06-A (5 shots) as one ref | (Alex, after watching) |
| T0015 | S05 | Track A ref2va: technicolor sheets + plate, WITH video ref | NEGATIVE — reads 2D rotoscope cel, not live-action |
| T0016 | S05 | ref2va AUDIO-ONLY (no video ref) + authored blocking + clean plate | register HOLDS; two people lounging, no crowd |
| T0017 | S03 | audio-only REF2VA, Ice Peak throne hall (Juliana/Nekron) | register holds; Nekron seated per blocking |
| T0018 | S03-c01 | FL2VA VLM-authored prompt (VLM describes actual first/last frames + ROSTER strings), vs T0003 template (same stills/seed/weight) | structural fix: position FLLL (was LLLL), frozen 25% (was 75%); verdict pending |
| T0019 | S03-c02..c05 | FL2VA VLM-prompt sweep, whole S03 throne-hall dialogue vs T0003 siblings (same stills/seed/weight) | renders 4/4 success; stitched scene + per-chunk compares built; verdict pending |
| T0021 | Krea2 sweep -> Qwen scene | identity hold: winner still -> Qwen scene still, 4 chars (darkwolf/taro/teegra/juliana), shared scene, same seed | HOLDS — same face/hair/costume on all 4 (contact sheet scenes/stills/t0021_identity_contact.jpg) |
| T0024 | darkwolf | H3 I2V A/B: bare sheet + text scene (old) vs Qwen scene still (new), same seed/graph | NEW holds the storm/megalith scene + identity through the clip; OLD stayed a misty void and added a weapon. scene-still path wins |
| T0022 | darkwolf | Qwen ref slots: image1 only vs +source film frame (ref3), same seed | register stays live-action technicolor in BOTH — the 1983 source frame did NOT drag it to 2D. ref3 safe to use for pose/framing |
| T0023 | darkwolf | Qwen scene framing: 4:3 (1280x960) vs 9:16 portrait (768x1368) | portrait composes a clean full-body (head+feet in frame) and matches the H3 9:16 downstream — made portrait the build_scenes default |

Browsable in the shot browser: `index.html?view=tests` — data generated
by `tools/build_testruns_data.py`, re-run it after copying new renders in.
Clips: `runs/<id>_*/output/`, `runs/testruns/` (copies from the 5090 drive),
plus `runs/T0008_*/` and `runs/T0009_*/` audio overlays.
