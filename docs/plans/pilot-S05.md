# Pilot: two passes — S05 "Teegra's lesson" + the abduction (S06-E)

Locked 2026-10-12; second pass added 2026-10-13 ("let's do both").
**Together: 4 setups, 4 characters, 16 shots, 7 chunks.** That is the whole brief —
Teegra, Tutor, Shaitan and the subhuman kidnapper — and neither scene holds all four
alone: the Tutor is in S05 only, the kidnapper in the abduction only, and **Shaitan
bridges the two** (passive on a cushion in S05, snarling at the intruders in the
abduction).

Pass 1 below is S05. Pass 2 is at the end of this file.

---

## PASS 1 — S05 "Teegra's lesson" (Fire Keep study)

Deliberately small: **3 characters, 3 setups, 9 shots, 4 chunks.**

Source: beat-sheet S05, 00:13:23–00:14:06, lines **L038–L048**.
Cast (beat-sheet): **Teegra, Tutor, Shaitan (pet)**. Location: Fire Keep study.
Music: light / wry.

## Setups (from `manifests/continuity_v2.jsonl` — the VLM clusterer, not v1)

v2 gives this scene a clean shot/reverse-shot structure; v1 fragments it into 6. `crosscut: true`,
6 alternations.

| Setup | Shots | Who / what |
| --- | --- | --- |
| **S05-A** | 00188 | opener — the room, no dialogue |
| **S05-B** | 00189, 00191, 00193, 00195 | **Teegra's side** of the exchange |
| **S05-C** | 00190, 00192, 00194, 00196 | **Tutor's side** of the exchange |

Sequence: A, B, C, B, C, B, C, B, C.

This is the scene's whole point as a pilot: two cross-cut setups (B and C) that must share ONE
master background plate each, rendered together for consistency, then split apart at assembly.
Exactly the "plan by setup, never by chronology" rule, on a scene small enough to finish.

## Shots and chunks (the render units)

| Chunk | Shots | Setup(s) | h3 s | Framing / angle | Motion | Lines | Speaker |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| S05-c01 | 00188, 00189 | A + B | 12.25 | wide/low → CU/eye | static, static | L038 | TUTOR |
| S05-c02 | 00190, 00191 | C + B | 9.42 | wide/eye → CU/eye | stands→lies down, static | L039, L040 | TUTOR |
| S05-c03 | 00192, 00193, 00194 | C + B + C | 15.08 | CU/low, CU/eye, MS/eye | static ×3 | L041–L044 | TEEGRA, TUTOR |
| S05-c04 | 00195, 00196 | B + C | 15.08 | CU/eye, MS/eye | static ×2 | L045–L048 | TEEGRA |

Total source 00:13:14.293–00:14:06.554 (52.3 s) → 4 chunks, longest 362 frames (the cap).

## Characters and reference status

| Character | Refs | Descriptor | Status |
| --- | --- | --- | --- |
| **TEEGRA** | 24 in `refs/characters/TEEGRA/` | roster ✓ (long black hair, pale skin, light purple two-piece, gold hoops) | ready |
| **TUTOR** | 9 in `refs/characters/TUTOR/` | **not approved** — roster says "no approved descriptor yet. Do not invent one from a VLM sentence" | refs exist, descriptor needed |
| **SHAITAN** | **candidates found** — `refs/characters/SHAITAN/candidates/` (3 crops, unapproved) | draft in `refs/characters/SHAITAN/note.txt` | **identified: a black feline**, not a human — needs Alex's approval |

**Shaitan identified (2026-10-12).** It is a **black feline** (big-cat scale, panther-like, glowing
yellow eyes, white whiskers, no collar or markings), present in the chamber during the lesson. Best
frames: shot 00190 (full body on a red cushion, nothing overlapping) and shot 00196 (head beside
Teegra's face — the shot where she says "Don't we, Shaitan?"). Candidates cropped and waiting in
`refs/characters/SHAITAN/candidates/`; identification is unconfirmed per the roster rule.

Voice: all 11 lines exist as clean wavs — `audio/lines/L038_TUTOR.wav` … `L048_TEEGRA.wav`
(TUTOR: L038–L044; TEEGRA: L041, L045–L048).

## What already exists

- `fullrun/graphs/S05-c01..c04.json` + `fullrun/prompts/S05-c01..c04.txt` — 3-field FL2VA graphs.
- `refrun/graphs/S05-c04.json` + `refrun/prompts/S05-c04.txt` — one 6-field REF2VA graph (dry run).
- `refs/S05-c04_ref.mp4` (8.5 MB) — the preprocessed reference clip for c04.
- Stills: 3 per shot in `stills/full/` for all 9 shots.
- `runs/setups_v2/` has the clusterer + `captions*.json` for this pass.

## What is missing before a render

1. **Shaitan.** No refs, no approved descriptor. Source frames from the film, then a descriptor
   (Alex approves, per the roster rule) — or decide Shaitan is off-screen and drop the line's
   subject (L048 is addressed to it, so it should be visible).
2. **Tutor descriptor.** 9 refs exist; the roster explicitly leaves the descriptor unapproved.
   Needed before a 6-field `subject_definitions` line can be written.
3. **Setup plates for S05-A/B/C.** `refs/setups/` currently holds only S06-A..E. Each setup needs
   one generated master plate (`{tag}_plate.jpg`) — the Frazetta matte painting, not the collage.
4. **refrun graphs for c01–c03** (only c04 exists).
5. **Note on the existing prompts:** `fullrun/prompts/S05-c01.txt` opens on "Three figures in dark
   purple hooded robes" for shot 00188 — **this is accurate, not a mislabel**: the stills confirm
   three hooded figures with glowing yellow eyes on a stone ledge under a starry sky, framed by a
   tower with a carved stone gargoyle. That is not the Fire Keep study. **Shot 00188 looks
   misassigned to S05** (the dialogue for the scene starts at 00:13:23; 00188 sits at 00:13:14).
   Check the boundary before rendering — it may belong to the tail of S04 or be an exterior insert.
   Separately, the Tutor is described in the prompt as "an older man in plain Fire Keep robes" while
   the VLM pass labels the reverse-shot figure as a woman with a short black bob — one of the two is
   wrong and needs a human eye.

## Render plan (setup-major, as the pipeline requires)

1. Approve Tutor + Shaitan descriptors; pull Shaitan refs.
2. Generate the three setup plates (S05-A/B/C) — one per camera position.
3. Build the 6-field REF2VA prompts for c01–c04 with the setup plate + character stills + the
   line wavs; validate against `docs/h3-official/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`.
4. Queue by setup: all of B together (00189/191/193/195), then all of C (00190/192/194/196),
   then A (00188). Reassemble chronologically by shot id.
5. Judge with `tests/seam_probe.py` and by eye.

## Scope — RESOLVED (2026-10-13): do both
Alex: "let's do both". So the pilot is two passes, and the arithmetic lands exactly on the
original brief — **4 setups, 4 characters**:

| | setups | shots | chunks | characters |
| --- | --- | --- | --- | --- |
| Pass 1 — S05 lesson | 3 (A/B/C) | 9 (00188–00196) | 4 | Teegra, Tutor, Shaitan |
| Pass 2 — abduction (S06-E) | 1 (E) | 7 (00214–00220) | 3 | Teegra, Shaitan, Subhuman |
| **total** | **4** | **16** | **7** | Teegra, Tutor, Shaitan, Subhuman |

S07 ("Teegra kidnapped", 30 shots, **10 setups** in v2) is deliberately OUT of this pilot — the
abduction beat itself is S06-E, one setup. S07 belongs to a later pass.

---

## PASS 2 — the abduction: setup S06-E

Source: S06, beat "Envoy & Abduction". Shots **00214–00220** (7 shots), chunks
**S06-c06 / c07 / c08**. Speaker list is **empty in all three chunks** — this is a silent action
beat (no dialogue to synthesise; alarm/action music only).

**One setup.** `continuity_v2` puts all seven shots in `S06-E` — the intrusion, the panther and
Teegra are all the same camera position/lighting as far as the clusterer is concerned. S06 overall
has 24 shots in 5 setups (crosscut, 8 alternations); A–D are the envoy/parley beat, E is ours.

| Chunk | Shots | h3 s | Framing / angle / motion (ledger) | Who |
| --- | --- | --- | --- | --- |
| S06-c06 | 00212, 00213, 00214 | 12.96 | wide/low static · wide/low **climbers ascending** · wide/low static | 2 · 3 · 3 — the intruders entering |
| S06-c07 | 00215, 00216, 00217 | 5.17 | medium/eye static · close-up/eye **mouth opening** · close-up/eye **panther moving forward** | 1 · 0 · 0 — Teegra startled, then Shaitan |
| S06-c08 | 00218, 00219, 00220 | 6.58 | close-up/eye rotating · close-up/low static · close-up/eye static | 0 · 0 · 1 — Teegra in fear |

The ledger already names the animal: **"mouth opening"** and **"panther moving forward"** are the
motion[] values on 00216/00217, and **"climbers ascending"** on 00213 is the subhumans coming in.
Motion can be seeded straight from these — no VLM guessing needed.

### Characters
| Character | Status |
| --- | --- |
| **TEEGRA** | ready — 23 refs |
| **SHAITAN** | candidates in `refs/characters/SHAITAN/candidates/`, incl. the two abduction frames (00216/00217) that are the best faces we have. Unapproved. |
| **SUBHUMAN** | **nothing** — no refs folder, no descriptor. `refs/roster.json` carries the names (SUBHUMAN / SUBHUMAN CAPTAIN / SUBHUMAN LEADER / SUBHUMANS) with empty refs. Must be sourced before this pass renders. |

### What already exists for S06-E (this pass is further along than S05)
- `fullrun/prompts/S06-c06.txt`, `S06-c07.txt`, `S06-c08.txt` and matching graphs.
- `refs/setups/S06-E_ref.mp4` (12.6 MB) and `S06-E_plate.jpg`.
- **But the plate is a collage, not the target:** `S06-E_plate.jpg` is 640×720 — that is the
  contact-sheet `tools/build_setup_refs.py` emits, not a generated Frazetta plate. Needs replacing.
- Stills: 3 per shot for all 9 shots involved.

### What is missing
1. **Subhuman refs + an approved descriptor** (the one hard blocker unique to this pass).
2. A **generated** S06-E plate (replacing the 640×720 collage).
3. `refrun` graphs for c06–c08 (only `fullrun` 3-field graphs exist).
4. Shaitan approval (shared with Pass 1).

### Order of work
1. Approve Shaitan from the candidates; source + approve the Subhuman.
2. Approve the Tutor descriptor (Pass 1 blocker).
3. Generate plates: S05-A/B/C and S06-E — `tools/plate_sketch.py` on the 4090 once the LM Studio
   tests are done; sketch each setup's framing, prompt the environment, feed the blue-gem carved
   furniture into the study plate.
4. Build 6-field `refrun` prompts for the 7 chunks; validate against
   `docs/h3-official/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`.
5. Render setup-major (all of B, then all of C, then A; then E), reassemble by shot id.
6. Judge with `tests/seam_probe.py` and by eye.
