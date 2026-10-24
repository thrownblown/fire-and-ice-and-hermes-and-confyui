# Character sheet status (generated 2026-10-24)

All sheets are the technicolor-register recipe: H3 ref2va still + `krea/retro-fantasy`
LoRA @1.05, identity from one staged still (`id_<NAME>.*`), template
`graphs/H3CharSheet_technicolor.json`, driver `tools/gen_char_sheet.py`.

## Done (17 characters, 19 sheet files)

Mains, generated 2026-10-23 ~13:14-13:25:
DARKWOLF, JAROL, JULIANA, LARN, NEKRON, OTWA, ROLIEL, SHAITAN, SPIRIT, TARO,
TEEGRA, TUTOR

Added 2026-10-24 (were the remaining sheetless characters that have any reference
material):

| character | identity still used | status |
|---|---|---|
| SUBHUMAN | `ComfyUI_00101_.png` (its own multi-view gen) | PROVISIONAL — see below |
| SUBHUMAN CAPTAIN | film still `shot_00414_f00000.jpg` | PROVISIONAL |
| SUBHUMAN LEADER | film still `shot_00415_f00000.jpg` | PROVISIONAL |
| ENVOY | `corpus/refs/envoy_shot_00075.jpg` | ok |
| ENVOYS | copy of ENVOY (same design) | ok |

## Assumptions to review

1. **The subhuman look is NOT officially approved.** `refs/characters/SUBHUMAN/note.txt`
   records it as "NOT APPROVED … needs a human eye". These three sheets fix a look by
   assumption so the pipeline can proceed; they are provisional and should be redone if
   Alex picks a different design (the note flags `shot_00119` — the hulk with the tooth
   necklace and cigar — as an unresolved candidate).
2. **SUBHUMAN returns 3 full-body views, not 4** (take 1 and take 2 both). H3 collapses
   the fourth view for this creature; the portrait and six swatch circles are correct.
   Acceptable, but a Qwen-2.1 pass would hold the 4th view if wanted.

## Not generated (9) — no reference material exists

ELDER, GUARDS, NARRATOR, OTWA?, RIDERS, SUBHUMANS, VILLAGE CHIEF, VILLAGE ELDER
(and ENVOYS is covered by ENVOY above).

None of these has a `refs/characters/<NAME>/` dir, and none was identified by the
naming pass (`manifests/character_names.jsonl` has 0 hits). NARRATOR is voice-only.
The rest are minor/group roles (1-2 dialogue lines each). A sheet for any of them
would be pure invention — to do it properly, first mine candidate frames from
`stills/full/` for the scenes they appear in (VILLAGE CHIEF/ELDER in S02; GUARDS,
RIDERS in S21; SUBHUMANS in S02/S07/S14), then stage `id_<NAME>.*` and run the driver.

## Location backgrounds

All 21 canonical locations have plates and are verified **figure-free** (a plate with
painted/statue figures makes H3 render phantom background people). Audit tool:
`tools/plate_figure_check.py` (32B VLM, judges the newest take).
