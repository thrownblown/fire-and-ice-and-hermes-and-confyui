# T0003 — S03 FL2VA (first/last frame), source stills

- Date: 2026-09-28
- One variable vs T0002: mode. T0002 = ref2v with character refs; this = fl2va with the
  chunk's first and last source stills as keyframes. Same chunks, same seed
  (1125345046553186), same lengths, same dialogue assignment.
- Weight: h3/minimax_h3_fl2va_pruned_int8_convrot.safetensors (official FL2VA).
- Node: MiniMaxH3ImageToVideo (first_frame/last_frame). No turbo LoRA branch.
- Prompt format: FL2VA instruction line + integrated_multimodal_description +
  overall_soundscape + non_diegetic_music. Keyframe captions written by local
  qwen3-vl-8b (LM Studio), stored in captions.json.
- Question: is fflf a viable final-pipeline mode — does anchoring both ends of the
  chunk hold composition and identity better than ref2v?

| chunk | shots | first frame | last frame | lines |
|---|---|---|---|---|
| s03-c01 | 00067 | shot_00067_f00000.jpg | shot_00067_f00127.jpg |  |
| s03-c02 | 00068 00069 | shot_00068_f00000.jpg | shot_00069_f00107.jpg |  |
| s03-c03 | 00070 00071 | shot_00070_f00000.jpg | shot_00071_f00138.jpg |  |
| s03-c04 | 00072 | shot_00072_f00000.jpg | shot_00072_f00111.jpg |  |
| s03-c05 | 00073 00074 | shot_00073_f00000.jpg | shot_00074_f00081.jpg |  |

## Verdict
(Alex, after watching.)
