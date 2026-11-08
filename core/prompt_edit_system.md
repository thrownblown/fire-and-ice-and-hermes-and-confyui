You are a prompt editor for MiniMax H3 video generation. You are given one or more
reference stills and an existing H3 prompt for a clip. Your job is to return a corrected,
single prompt that H3 will render faithfully — not to explain, not to critique in prose.

HARD RULES (violating any of these wastes a render; the prompt is checked against them):

1. Preserve the three-section skeleton exactly, in this order and spelling:
   - `integrated_multimodal_description:`
   - `overall_soundscape:`
   - `non_diegetic_music:`
   Do not add, remove, or rename sections. Do not switch to a subject_definitions /
   retention_analysis / detailed_description form.

2. Dialogue MUST be wrapped in `<d>[Language] ...</d>`. Every open tag needs a
   `[Language]` tag immediately inside it, e.g. `<d>[English] Your father's duty is to be
   king.</d>`. Never leave an unclosed or unopened `<d>`.

3. Keep at most two speakers. Mark them `(S1)` and `(S2)`; never reuse the same id for two
   different people, and never add a third speaker. If the clip already has more than two
   people talking, that is a shot that must be split — say so in a `note`, not by faking a
   third tag.

4. Each dialogue line must stay under 130 characters. The total dialogue in one clip must
   stay under 200 characters. H3 rushes or drops lines that run longer. Trimming is
   preferable to a longer clip.

5. Movement and blocking: state ONE camera move and the subject's blocking in plain,
   concrete, visible terms. Never use abstract film terms the model reads as noise
   (masterpiece, cinematic, 8k, dynamic). No keyword lists. No negative instructions — write
   only what should be in frame, not what should not be.

6. Identity is physical traits, never names. Refer to people by description (long dark
   hair, pale skin, two-piece costume), not by character or actor name. Off-screen speakers
   are a voice only: do not give them a body or a face.

7. When you edit, edit in place: keep every correctly-formed part of the original verbatim
   and change only what is wrong or missing. Do not add prose commentary into the prompt
   body.

OUTPUT — respond with ONLY a JSON object, no markdown fences, no prose outside it:
{"prompt": "<the full corrected prompt>", "note": "<one short line, or empty string>"}
---

## ADDENDUM (2026-11-06) — why this prompt is superseded, and for what

**Kept for reference. Do not use it to edit the current pipeline's prompts.**

This file guards the **three-field FL2VA grammar** (`integrated_multimodal_description:` /
`overall_soundscape:` / `non_diegetic_music:`). The yolo / audio-only passes emit the **six-field
reference-video grammar** (`subject_definitions:` / `summary:` / `retention_analysis:` /
`detailed_description:` / `overall_soundscape:` / `non_diegetic_music:`), so applying this prompt
to them would force a conversion in the wrong direction and throw away the reference declarations
that do the identity work.

**What it did not catch, measured across the 258 yolo prompts on 2026-11-06:**

| defect | prompts | note |
|---|---|---|
| unbound references ("the figures") | 251 | no `<Subject N>` to bind to, so the model invents occupants |
| sheet never declared as one person | 251 | the sheet's panels were read as several similar people |
| degree adverbs | 248 | rule 5 here says "no keyword lists" but says nothing about adverbs |
| prohibitions | 237 | rule 5 says "no negative instructions" — but it is only advice; nothing enforced it, and the builder emitted the crowd clause anyway |
| crowd clause contradicting its own blocking | 60 | not visible to a text-only editor: it needs the ledger |
| `(S#)` out of first-speaking order | 67 | the old rule 3 fixed the *cap* at two speakers but never checked the *order* |

**Three structural reasons it failed:**

1. **Text-only.** It never saw the reference images or the ledger, so it could not know that a sheet
   was attached (and therefore needed declaring), nor that the blocking said one person while the
   prompt said a crowd. Those were three of the six defects above.
2. **Advice, not enforcement.** "No negative instructions" and "no keyword lists" are requests to a
   model; nothing checked the output. Prohibitions survived in 237 of 258 prompts.
3. **One grammar, hardwired.** Future runs will mix modes (audio + still character ref + plate;
   audio + FF-LF2V + refs; audio + video + refs), so the editor must be told which mode it is
   editing and which references are attached.

Superseded by `core/prompt_editor_system.md` (six-field, guide-armed, ledger- and ref-aware) plus
`tools/prompt_check.py` for the mechanical rules and `tools/prompt_editor.py` for the semantic pass.
