# Narrative thruline: local model job pack

**Goal:** a clear story spine before any more prompt generation. Local models on the 4090 do the bulk reading; GhstClwd (Opus) synthesizes the results into `narrative-thruline.md`.

## Run (on the 4090, from the project folder)
```
python narrative_jobs.py                                 # default model qwen3.8-27b-obliterated, all lanes
python narrative_jobs.py --model gemma-4-26b-a4b-it-heretic --lanes A   # optional second opinion
```
Stdlib only. Skips files that already exist, so it's safe to re-run. About 50 calls total.

## Lanes
| Lane | Calls | Output | What it answers |
|---|---|---|---|
| A: Scenes | 26 | `narrative/A-scenes/Sxx.md` | what happens, who wants what, stakes, the turn, hand-off to the next scene, visual beats needed, confusions |
| B: Characters | 7 | `narrative/B-characters/NAME.md` | want vs need, arc with scene ids, relationships, gaps, logline (Larn, Teegra, Nekron, Juliana, Darkwolf, Jarol, Taro) |
| C: Silent stretches | 9 | `narrative/C-gaps/before-Sxx.md` | what must happen in the no-dialogue stretches, a hypothesized beat list (checked against footage later), continuity |
| D: Cut ending | 1 | `narrative/D-cut-ending.md` | how "Darkwolf = Nekron's father" reframes the story, foreshadowing spots, a shot list for the restored ending |

Every prompt says "use only the provided text; label inferences ASSUMPTION" so the models don't fill gaps from half-remembered versions of the film.

## Then
Zip or send the `narrative/` folder back and I'll write `narrative-thruline.md`: a one-page spine, act structure, per-scene purpose, and character arcs. That feeds the beat sheet and the `# prev / # next` lines in every H3 prompt.
