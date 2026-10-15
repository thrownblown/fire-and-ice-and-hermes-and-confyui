# Prompt-crafter input contract — script + captions + canon

Date: 2026-10-15. Status: draft for Alex review. Alex (OptMem i=111): "the final
prompt crafter will have to take the SCRIPT and the CAPTIONS into account."

This is the downstream consumer spec for the H3 prompt writer (refrun 6-field /
fullrun 3-field, and the Krea2 stills prompt step). It fixes, field-by-field, what
each prompt field reads from, so no field is ever sourced from the wrong place and
nothing is invented at craft time.

## Why three sources, not one

- **Script** pins INTENT: who speaks, the verbatim line, and the emotion/action the
  line implies. This is the only source for dialogue and expression direction.
- **Captions** pin COMPOSITION: pose, framing, setting, on-screen action. Physical
  only; the q4 VLM is wrong about emotion and color, so captions never feed those.
- **Canon** pins IDENTITY: the settled per-character traits (Teegra = green eyes /
  pale skin / long black hair / purple two-piece / gold necklace). Overrides the VLM
  on color every time.

## Source 1 — script (`script/dialogue-timeline.tsv`)

Header: `id  scene  cue  start  end  speaker  conf  text`

Contract fields the crafter reads:

| field | source col | use |
|---|---|---|
| `speaker` | speaker | subject stamp / `<Subject N>` binding (voice-only if off-screen) |
| `text` | text | verbatim dialogue — NEVER paraphrased, placed inside `<d>[Language] ... </d>` |
| `scene` + `cue` | scene, cue | which chunk owns the line (a line maps to the shot containing its midpoint) |
| `conf` | conf | delivery emphasis in `detailed_description`: HIGH = projected/forceful, LOW = close/murmured. Not an emotion, only volume+intensity. |
| `intent` | intent | the human-stated emotional/actional reading of the line (added 2026-10-15; empty until filled). When present, it is the crafter's expression source and outranks any inference from the line's words alone. |

Rule: a line's midpoint timecode → its shot → its chunk (see chunk ledger below).
A line assigned to a speaker not on screen is voice-only (no face, no body).

## Source 2 — captions

Two caption families exist; they serve different fields:

A. **Lens captions** — `library/char/vlm-cache/<CHAR>/<lens>/<image>.json`,
   aggregated to `library/char/profiles/<CHAR>.json` (stable >= 0.6 / disputed).
   Feeds the character's *canonical* appearance when no canon override exists:
   build, height impression, face shape, hair length/texture/style, wardrobe
   garments, props/weapons.

B. **Composition captions** — the per-frame translation captions
   (`manifests/teegra_translate_captions.jsonl`: pose / action / expression-free /
   setting / framing). Feeds `detailed_description` composition. This is what made
   the stills-translation pass; the H3 crafter reads the SAME file so stills and
   video agree on composition.

Explicitly NOT read from captions: eye color, skin tone, hair color, garment color,
emotion/expression. Those come from canon (3) and script (1) respectively. The q4
VLM reports brown eyes / brown-tan skin / drifts expression — all three are known
wrong and are overridden downstream.

## Source 3 — character canon

- `refs/characters/<NAME>/traits.txt` — the settled identity string (one line).
  This is the single source of truth for color and costume. VLM-reported color
  outranks a *user-typed* color in general, but a canon line Alex has settled
  (Teegra green eyes / pale skin) outranks the VLM.
- `refs/roster.json` → `traits` field — machine-readable copy of the same canon.

## Chunk binding (the join key)

The crafter works one chunk at a time. `fullrun/chunks.jsonl` is the spine; each
chunk row already carries the join fields it needs, so the crafter must read them
rather than re-deriving:

| chunk field | meaning | feeds prompt field |
|---|---|---|
| `shot_nums[]` | shot ids in this chunk | which stills/frames to caption-source |
| `speakers[]` + `line_ids[]` | who speaks, which script lines | dialogue + speaker stamps |
| `motion[]`, `shot_type[]`, `angle[]` | per-shot camera + action | `detailed_description` camera terms + physical action |
| `stamped_names[]` | pre-bound subject names | `<Subject N>` identity anchors |
| `cast[]`, `location` | who's present, where | subject_definitions + environment wording |

Rule carried from the skill: dialogue comes from the timeline TSV, never from ASR
and never from who the vision pass happened to see.

## Output grammar (unchanged — the contract only fixes INPUTS)

- REF2VA (Track A, 6-field): `subject_definitions / summary / retention_analysis /
  detailed_description / overall_soundscape / non_diegetic_music`.
- FL2VA (Track B/C, 3-field): `integrated_multimodal_description /
  overall_soundscape / non_diegetic_music`.

Both grammars stay as documented; this contract only says WHERE each input to those
fields comes from, so the crafter stops sourcing identity from captions and emotion
from nowhere.

## Handoff to the edit-model pass (wardrobe/props are NOT the crafter's job)

The crafter does not try to nail wardrobe or props in the Krea prompt — Krea drifts
on garment detail even at fixed seed+prompt+LoRA (the Teegra bikini-top case). The
prompt-crafter contract therefore ends at composition + identity + intent, and hands
off to the edit-model stage (see `docs/plans/2026-10-15-krea-to-edit-shot-pipeline.md`
and the asset schema `docs/asset-schema.md`) for garment/prop correctness.

Concretely, the crafter emits for each shot:

| field | content | correctness owner |
|---|---|---|
| `character_prompt` | canonical identity ONLY (face/hair/eye/skin from canon, never read off the 1983 palette) | crafter |
| `scene_description` | composition, framing, camera, action from captions + chunk ledger | crafter |
| `rough_wardrobe_desc` | loose, deliberately-approximate garment/prop text — will be corrected by the edit pass | crafter (placeholder only) |
| `style_lora` | house style (retro-fantasy @1.0; jada char LoRA OFF) | crafter |

Stage 1 (Krea generate) then runs free on `character_prompt + scene_description +
rough_wardrobe_desc`; the human approves composition/pose/lighting/likeness in Stage 2;
Stage 3 (Qwen-Edit, primary) swaps in the canonical garment/prop from the asset library
using its `approved` references. The crafter is explicitly relieved of wardrobe/prop
correctness — its rough text is a hint, not a spec. This is the "generate with Krea, then
edit-model swap" handoff Alex specified on the kanban (t_72b35a1d).

## Open items for Alex

Resolved 2026-10-15 ("do it"):

1. `conf` maps to delivery emphasis (HIGH = projected/forceful, LOW = close/murmured) in
   `detailed_description` — volume + intensity only, never an emotion label.
2. `intent` column added to `script/dialogue-timeline.tsv` (empty, CRLF preserved). The
   crafter reads it as the authoritative expression/mood for the line; where empty it
   falls back to the line's words. This is the one place a human (or a later
   script-aware pass) states the reading.
