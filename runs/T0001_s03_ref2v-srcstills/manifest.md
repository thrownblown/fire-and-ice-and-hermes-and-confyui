# T0001 — s03 ref2v, original stills

- Date: 2026-09-27
- Scope: S03, chunks s03-c01 s03-c02 s03-c03
- Method: ref2v. v3 prompts. Original stills as identity refs. No Frazetta styling, no location plate, no blocking frame.
- Question: does the v3 prompt structure fix plot and speakers?
- Workflow: graphs/video_minimax_h3_r2v.json
- Model: h3/minimax_h3_ref2va_pruned_int8_convrot.safetensors
- CLIP: qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
- Sampler: res_multistep, simple, 20 steps. Lightning LoRA off.
- Seed: 1125345046553186 (same for all three takes)
- One variable vs later tests: the refs. T0002 swaps in styled sheets. Nothing else changes.

## Chunks
| chunk | duration | lines | takes |
|---|---|---|---|
| s03-c01 | 14.4s | L023-L026 | t01 |
| s03-c02 | 13.7s | L027-L031 | t01 |
| s03-c03 | 8.0s | L032-L033 | t01 |

## Refs (original stills, not library versions)
- JULIANA: juliana_portrait.jpeg, juliana_chains.jpeg
- NEKRON: nekron_shot_00068.jpg, nekron_shot_00070.jpg (mid frames of those shots)
- ENVOY: envoy_shot_00073.jpg, envoy_shot_00075.jpg (c03 only)

## Verdict
Decent. Alex, 2026-09-27, after watching the takes. Plot and speakers held well enough to keep this as the baseline. Not a final. T0002 still has to show whether styled refs carry into the motion.
