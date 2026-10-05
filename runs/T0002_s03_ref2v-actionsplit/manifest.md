# T0002 — S03 ref2v, split at action beats

- Date: 2026-09-27
- One variable vs T0001: chunk size. T0001 had 3 chunks. This has 5, split where the action changes.
- Same refs, same seed (1125345046553186), same model, same sampler as T0001.
- Question: does a smaller action beat stop the glitches a long prompt causes?

| chunk | shots | lines |
|---|---|---|
| s03-c01 | 00067 | L023 L024 |
| s03-c02 | 00068 00069 | L025 L026 |
| s03-c03 | 00070 00071 | L027 L028 L029 |
| s03-c04 | 00072 | L030 L031 |
| s03-c05 | 00073 00074 | L032 L033 |

## Verdict
Alex, 2026-09-28: pretty good. On the right track. The action-beat split holds.
