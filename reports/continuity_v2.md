# Setups v2 — continuity re-clustering (local VLM, relative grouping)

Replaces v1's grayscale-SSIM first-frame clustering (setup-th=0.42) with
semantic camera-setup grouping. Each scene's boundary stills are fed to
qwen2.5-vl-32b (LM Studio, `--gpu 0.8 -c 8192`) which groups them into
setups directly — same camera position + same background = same setup,
pose/action ignored. Replaces the SSIM failure mode: v1 could not express
"same camera angle, different actor pose", so dialogue scenes fragmented
to ~1 setup per shot.

## Summary

- Shots: 1308 across 34 scenes
- Setups: 968 (v1) -> 704 (v2)  —  264 fewer (27%)
- Multi-shot setups (recurrences correctly merged): 121 -> 307  —  +186
- Cross-cut scenes: 8 -> 18
- Newly flagged cross-cut: G06, S03, S05, S15, S18, S20, S22, S23, S24, S25

## Per-scene comparison

| Scene | Shots | v1 setups | v2 setups | d | v1 multi | v2 multi | alt | cross-cut |
|---|---|---|---|---|---|---|---|---|
| G01 | 39 | 23 | 13 | -10 | 3 | 12 | 6 | yes |
| G02 | 110 | 72 | 83 | +11 | 14 | 23 | 13 | yes |
| G03 | 157 | 104 | 117 | +13 | 14 | 34 | 11 | yes |
| G04 | 49 | 31 | 10 | -21 | 3 | 8 | 9 | yes |
| G05 | 22 | 22 | 15 | -7 | 0 | 6 | 3 |  |
| G06 | 32 | 27 | 11 | -16 | 5 | 11 | 5 | new |
| G07 | 47 | 36 | 20 | -16 | 6 | 16 | 1 |  |
| G08 | 149 | 119 | 110 | -9 | 6 | 29 | 10 | yes |
| G09 | 78 | 63 | 57 | -6 | 5 | 18 | 3 |  |
| S01 | 15 | 6 | 7 | +1 | 2 | 4 | 1 |  |
| S02 | 12 | 8 | 5 | -3 | 2 | 3 | 2 |  |
| S03 | 8 | 5 | 3 | -2 | 2 | 2 | 5 | new |
| S04 | 3 | 3 | 2 | -1 | 0 | 1 | 1 |  |
| S05 | 9 | 6 | 3 | -3 | 2 | 2 | 6 | new |
| S06 | 24 | 15 | 5 | -10 | 6 | 5 | 8 | yes |
| S07 | 30 | 29 | 10 | -19 | 1 | 4 | 3 |  |
| S08 | 6 | 3 | 2 | -1 | 2 | 1 | 0 |  |
| S09 | 11 | 9 | 3 | -6 | 2 | 3 | 2 |  |
| S11 | 81 | 41 | 57 | +16 | 6 | 23 | 10 | yes |
| S12 | 18 | 16 | 8 | -8 | 2 | 4 | 3 |  |
| S13 | 18 | 18 | 8 | -10 | 0 | 7 | 2 |  |
| S14 | 27 | 19 | 20 | +1 | 2 | 4 | 0 |  |
| S15 | 14 | 10 | 5 | -5 | 3 | 3 | 5 | new |
| S16 | 28 | 27 | 8 | -19 | 1 | 7 | 2 |  |
| S17 | 39 | 27 | 9 | -18 | 4 | 9 | 12 | yes |
| S18 | 17 | 13 | 6 | -7 | 2 | 4 | 8 | new |
| S19 | 13 | 13 | 6 | -7 | 0 | 5 | 3 |  |
| S20 | 43 | 36 | 12 | -24 | 6 | 8 | 9 | new |
| S21 | 70 | 54 | 45 | -9 | 10 | 22 | 2 |  |
| S22 | 60 | 46 | 18 | -28 | 4 | 13 | 6 | new |
| S23 | 13 | 10 | 6 | -4 | 2 | 4 | 4 | new |
| S24 | 16 | 12 | 5 | -7 | 2 | 4 | 5 | new |
| S25 | 39 | 38 | 9 | -29 | 1 | 5 | 8 | new |
| S26 | 11 | 7 | 6 | -1 | 1 | 3 | 0 |  |

## Biggest changes

Most fragmentation fixed (v1 over-split -> v2 re-merged recurrences):

- S25: 38 -> 9 setups (39 shots; multi-shot 1 -> 5)
- S22: 46 -> 18 setups (60 shots; multi-shot 4 -> 13)
- S20: 36 -> 12 setups (43 shots; multi-shot 6 -> 8)
- G04: 31 -> 10 setups (49 shots; multi-shot 3 -> 8)
- S07: 29 -> 10 setups (30 shots; multi-shot 1 -> 4)
- S16: 27 -> 8 setups (28 shots; multi-shot 1 -> 7)
- S17: 27 -> 9 setups (39 shots; multi-shot 4 -> 9)
- G06: 27 -> 11 setups (32 shots; multi-shot 5 -> 11)
- G07: 36 -> 20 setups (47 shots; multi-shot 6 -> 16)
- G01: 23 -> 13 setups (39 shots; multi-shot 3 -> 12)
- S06: 15 -> 5 setups (24 shots; multi-shot 6 -> 5)
- S13: 18 -> 8 setups (18 shots; multi-shot 0 -> 7)

Went up (gap/montage scenes where v1's SSIM over-merged distant frames;
v2 splits them into more distinct backgrounds):

- S11: 41 -> 57 setups (81 shots; multi-shot 6 -> 23)
- G03: 104 -> 117 setups (157 shots; multi-shot 14 -> 34)
- G02: 72 -> 83 setups (110 shots; multi-shot 14 -> 23)
- S01: 6 -> 7 setups (15 shots; multi-shot 2 -> 4)
- S14: 19 -> 20 setups (27 shots; multi-shot 2 -> 4)

## Known limitations (local-only)

- The 32b merges SOME reverse angles and some distinct-but-similar
  backgrounds (e.g. S02 rolls five cold backdrops into one setup). This is
  the accepted cost of the local pass; SSIM and both local VLMs measurably
  cannot split reverse angles — only a strong cloud VLM does (see the
  vlm-image-labeling skill).
- Partial-model-output salvage: where the 32b returned an incomplete
  grouping, omitted shots are kept as singletons rather than dropped.
- `edges` (chain/cut SSIM adjacency) are backfilled from v1 unchanged — that
  signal was never the broken part.

Generated from manifests/continuity.jsonl (v1) vs manifests/continuity_v2.jsonl (v2).
