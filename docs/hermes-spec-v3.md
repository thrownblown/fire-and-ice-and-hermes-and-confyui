# Fire and Ice — Pipeline Spec v3

*2026-09-26. Replaces v2 and its amendments. Written by GhstClwd for Hermes on the 4090.*

## Why v3

The v2 run produced prompts with no plot and repeated/misattributed dialogue:
- Every line was spoken by `<Subject 1>` (Juliana's, Nekron's, Jarol's, and the Tutor's lines all came out of Teegra).
- The roster only had Larn, Teegra, and Nekron. Everyone else was "the figures."
- Most chunks had no dialogue, and some lines were cut mid-sentence.
- Shot timing was a template (0 / 2.5 / 5.0s, "camera pushes in slowly") regardless of the real cuts.
- Locations were labeled per shot, so one throne room was called three different things.
- Shots described places with no action.
- Chunk numbers had gaps.

**Root cause:** the pipeline went shot → VLM → guess the script. v3 inverts it. **The script and timecodes are the spine; shots and the VLM only fill in visuals.**

## Principles

1. **Script first.** Dialogue, speaker, order, and scene come from the timeline file. The VLM never decides who speaks or what the scene is.
2. **Every line is used exactly once, in order.**
3. **Every step produces a Markdown file Alex can read.** Tables for data, `![](path.jpg)` for frames. No HTML, no JSON-only intermediates.
4. **One scene end-to-end before scaling.**
5. No database, no web app, no abstraction layers. No new tests except the validator. Keep the existing grouping-rule tests.

## Provided inputs (already done, in `projects/fire-and-ice-remake/`)

| File | What it is |
|---|---|
| `script/fire-and-ice-1983.srt` | English subtitles, timed to the 1080p release |
| `script/dialogue-timeline.tsv` | **Source of truth.** 290 lines: `id, scene, cue, start, end, speaker, conf, text` |
| `script/dialogue-timeline.md` | Same thing, human-readable, grouped by scene |
| `beat-sheet.md` | 26 scenes (S01–S26): time range, line IDs, cast, canonical location, music |

37 speakers are `conf=LOW`. Alex verifies those before Stage 3 runs on the affected scenes. S03 has none.

**Check first:** confirm Hermes' video file and the SRT share a timebase. Spot-check 3 lines (e.g. L001 at 00:02:41, L023 at 00:06:56, L290 at 01:17:14) against the audio. If there's an offset, apply one global shift and note it in `00-sync-check.md`.

## Line vs cue (clarification)
- A **cue** is one SRT subtitle. A **line** is one speaker's utterance.
- 21 cues hold two speakers ("- X - Y"). The timeline already splits each of those into two line IDs that share the same cue number and cue timecode. That's why 269 cues become 290 lines.
- Hermes uses the provided line IDs as-is. Don't re-split or re-merge.
- "Never split a line" means: don't break one line across shots or chunks.
- Two lines that share a cue always go in the **same shot and same chunk** (they're an exchange by definition). Assign both by the cue midpoint.

## Roster

Every speaking or recurring character gets an ID, a visual descriptor, and **up to 6 reference stills** (clean frames only, no burned-in captions). Alex picks or approves the refs.

| ID | Character | Descriptor (confirm/fill from refs) |
|---|---|---|
| LARN | Larn | blond, muscular, brown belt with gold buckle, bone necklace |
| TEEGRA | Teegra | long black hair, light purple two-piece, gold earrings |
| NEKRON | Nekron | pale, long white hair, dark purple robe |
| JULIANA | Queen Juliana | TBD. Must be visually distinct from Teegra (crown/regalia/robes) |
| DARKWOLF | Darkwolf | wolf-head helm/mask, battle axe. TBD details |
| JAROL | King Jarol | TBD |
| TARO | Prince Taro | TBD |
| ROLIEL | Roliel (witch) | TBD |
| OTWA | Otwa | TBD, huge and strong |
| TUTOR, ENVOY, SPIRIT, SUBHUMAN(S), VILLAGE CHIEF/ELDER | minor | TBD |
| NARRATOR | voice only | never on screen |

Output: `01-roster.md` with a descriptor and ref thumbnails per character.

---

## Stages

### Stage 1: Scene cut map
For the target scene's time range (from the beat sheet, padded by ±5s), list every scene-detect cut: shot number, start, end, duration, start/mid/end thumbnails.
**Output:** `sNN/1-shots.md`

### Stage 2: VLM visual pass (per shot)
Model: `qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s` at localhost:1234. Sequential or 2 at a time.

Prompt (constrained, **no names, no locations**):
```
You are looking at 3 frames (start, middle, end) of one shot from a 1983 animated film.
Answer in this exact format:
PEOPLE: <count>
PERSON n: <sex>, <hair>, <clothing>, <position in frame>, <what they are doing, one verb phrase>
CAMERA: <shot size: extreme close-up/close-up/medium/wide/extreme wide>, <angle>, <movement: static/pan/tilt/push/pull/track>
ACTION: <one sentence describing what happens from first to last frame>
Do not guess names. Do not name the location.
```
Then map PERSON n to roster IDs by **scene cast list + descriptor match**. If a person doesn't match anyone in the scene's cast, mark them `?`. Don't pull characters from outside the scene.
**Output:** `sNN/2-visuals.md`: thumbnails, raw VLM answer, mapped roster IDs. Alex corrects the `?`s.

### Stage 3: Line → shot assignment (deterministic)
- A line belongs to the shot that contains the **midpoint** of its timecode.
- Lines spanning a cut stay whole and go to the shot holding their midpoint. Never split a line.
- The speaker comes from the timeline. If the speaker isn't visible in the shot, that's fine: mark it `(off-screen)` / `(V.O.)`.
- Shots with no lines are action shots.
**Output:** `sNN/3-assignment.md`: shot | time | on-screen roster IDs | lines (ID, speaker, text) | action.

### Stage 4: Chunking
- 2–3 consecutive shots per chunk, within H3's max duration.
- Never split an exchange: if L(n) and L(n+1) are a question/answer within ~1.5s, they go in the same chunk.
- **Never cross a scene boundary.**
- Chunk IDs are `sNN-cMM`, sequential, no gaps.
**Output:** `sNN/4-chunks.md`

### Stage 5: H3 prompts (ref2v)
One file per chunk: `sNN/prompts/sNN-cMM.txt`. Keep Hermes' existing field layout, but fill it from the scene/timeline data:

```
# chunk: s03-c02 | scene: S03 Ice Peak: Juliana & Nekron send envoys
# source: 00:06:58.9–00:07:05.4 | lines: L024–L025
# prev: Juliana praises Nekron's victory. | next: Nekron plans to send envoys.

subject_definitions:
<Subject 1>: JULIANA, <descriptor>. Seen in <Picture 1>, <Picture 2>.
<Subject 2>: NEKRON, <descriptor>. Seen in <Picture 3>, <Picture 4>.
<Picture n>: ... (up to 6 total; do not import pose/action)

summary: reference generation + audio reference

retention_analysis:
<Subject 1> (appears in [Shot 1]): attribute_transfer
<Subject 2> (appears in [Shot 2]): attribute_transfer

detailed_description: rotoscope painted animation. <CANONICAL LOCATION from beat sheet>. <lighting>.
[Shot 1] (0.0s) <CAMERA from VLM>. <ACTION with a verb>. <Subject 1> says, <d>[English] The North Village has fallen. We have won.</d>
[Shot 2] (<real offset>s) <CAMERA>. <ACTION>. <Subject 2> says, <d>[English] I want to thank you, Mother.</d>

overall_soundscape: <from scene: e.g. cavernous hall reverb, distant wind>
non_diegetic_music: <music cue from beat sheet>
```

Rules:
- `<Subject n>` in a `says` must be the timeline speaker. Off-screen speakers still get defined as a subject, with their line marked `(off-screen)`.
- Narrator lines: `Narrator (V.O.) says, <d>...</d>` with no subject definition.
- Shot offsets = real cut times relative to the chunk start. Never 2.5 / 5.0 placeholders.
- Location string = the beat sheet's canonical location, identical across every chunk in the scene.
- Full dialogue text, never truncated.

**Output:** the prompt files plus `sNN/5-review.md` (each prompt next to its source thumbnails).

### Stage 6: Validator
`validate.py sNN` writes `sNN/6-validation.md` with ✅/❌ per check:
- every line ID in the scene's range appears in exactly one chunk
- line order never goes backwards
- chunk IDs are sequential with no gaps
- no chunk spans two scenes
- every `says` speaker = the timeline speaker, and is defined in subject_definitions (or is the Narrator)
- no `<d>` text is shorter than the timeline text (catches truncation)
- no placeholder offsets (every shot has a real offset)
- location string is identical across the scene's chunks

Nothing goes to H3 until everything is ✅.

### Stage 7: Generate + stitch
Generate the chunks, stitch them in order, and export `sNN-stitched.mp4`. Alex watches it. **That is the real test.**

---

## First target: S03, Ice Peak (Juliana & Nekron send envoys)

Lines L023–L033 · 00:06:56–00:07:32 · cast JULIANA, NEKRON (+ envoys) · location "Ice Peak throne hall"

| ID | Time | Speaker | Line |
|---|---|---|---|
| L023 | 00:06:56 | JULIANA | You have done well, my son. |
| L024 | 00:06:59 | JULIANA | The North Village has fallen. We have won. |
| L025 | 00:07:03 | NEKRON | I want to thank you, Mother. |
| L026 | 00:07:05 | NEKRON | The Great Plain is all that stands between ourselves and Fire Keep. |
| L027 | 00:07:10 | JULIANA | That is a long distance. |
| L028 | 00:07:13 | NEKRON | A distance we may not have to travel. |
| L029 | 00:07:16 | NEKRON | I am sending our envoys to Jarol with our new demands. |
| L030 | 00:07:20 | JULIANA | He will not submit. |
| L031 | 00:07:20 | NEKRON | Perhaps. |
| L032 | 00:07:24 | NEKRON | You will present our demands to King Jarol at Fire Keep and... |
| L033 | 00:07:28 | NEKRON | give our royal regards to his lovely daughter. |

It's short, two speakers, alternating, and exactly where v2 broke (all of this was attributed to Teegra). If S03 plays back correctly, run S04–S06, then the rest.

## Later
- Long no-dialogue stretches (see the beat sheet, e.g. 00:17–00:25) need action beats from Stage 2 plus Alex's review. No script exists for them.
- S25 carries the cut Darkwolf parentage scene. It's written from scratch, since there's no footage.

## Do not
- Let the VLM name characters or locations
- Assign a speaker by who's visible
- Use placeholder timing
- Merge/split lines or paraphrase dialogue
- Chunk across scenes
- Run the whole film before one scene plays back correctly
- Produce HTML or JSON-only artifacts
