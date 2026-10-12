# Plan — ref2va action test clips (setup-style prompts)

Date: 2026-10-11. Status: planning.

## Goal
Validate the ref2va setup and the setup-style prompt grammar on ACTION content before
committing to a scene-length automated run. Action clips stress everything the static
Teegra/chaise tests did not: fast whole-body motion, props (swords, spears), multiple
subjects, animals, and physical stunts. If the prompt/setup survives those, the 6-field
grammar is trustworthy.

## Method
- Manual runs of the altoiddealer "Simply Advanced" workflow first — get the MODEL lineup
  and node config correct by hand, one clip at a time, before wiring anything automated.
  (Per the veterans thread, model/LoRA mistakes are the #1 cause of bad ref2v output.)
- Each test isolates ONE variable and produces a watchable verdict, not a metric.
- One clip per chunk, ref video = `refs/<chunk>_ref.mp4` (24fps, preprocessed).

## Setup variables to pin by hand (the order to get right)
1. Diffusion model: base `ref2va_pruned_int8_convrot` (fidelity) vs hybrid (quality).
2. Text encoder: `qwen3vl_32b_minimax_h3_nvfp4_awq` (ours) vs `..._int4_convrot` (WF default).
3. Turbo LoRA: OFF (full steps) vs 0.4 strength vs 4-step@1.0 — the veterans thread says
   4-step@1.0 is the quality-killer; prove it on our content.
4. ref_image_size: `match` vs `max`.
5. Scheduler/sampler: `simple`+`res_multistep` (ours) vs `er_sde` / `sgg_uniform` (community).
6. Spectrum speedup: on/off.

## Candidate action clips (from the chunks ledger)
Chosen to span the distinct stress dimensions. Each is a real chunk with a preprocessed ref.

| chunk  | scene | shots | secs | content | stresses |
|--------|-------|-------|------|---------|----------|
| S21-c20 | S21 | 879–881 | 6.58 | NEKRON moves sword, changes hand position + expression | prop adherence (sword), hand/facial detail, single named subject |
| S21-c19 | S21 | 876–878 | 11.54 | NEKRON gesturing and raising sword; 3 shots | prop + multi-shot temporal structure, named subject |
| S19-c01 | S19 | 770–772 | 10.83 | LARN: man running; medium/wide/medium | whole-body locomotion + camera change |
| S22-c03 | S22 | 902–904 | 8.71 | person being thrown from cliff edge; low/eye/wide | violent physics, big stunt, no dialogue |
| S19-c03 | S19 | 776–778 | 12.25 | riders moving across frame; high/eye/medium | animal (horse) + multi-subject + high angle |
| G04-c09 | G04 | 446–448 | 5.88 | person moving forward, creatures running; all wide | crowd/creatures, pure action, no dialogue |
| S07-c07 | S07 | 237–239 | 4.46 | figure being thrown to ground; close/medium/medium | short clip, impact, no dialogue |

Recommended first three (each isolates a different axis):
1. **S21-c20** — single subject + prop, nearest to what we've already tested (Teegra) but adds
   a held weapon. The prompt-vs-prop-adherence test.
2. **S19-c01** — LARN whole-body run, no dialogue. Tests motion transfer + identity on a
   fast-moving subject (the vets' "use the video to drive the motion" claim).
3. **S22-c03** — a violent cliff throw. Tests big physics the model was NOT shown how to do
   in the ref (only 3 frames of motion); the hardest extrapolation.

Hold S19-c03 (horse) and G04-c09 (creatures) for a second round — animals/crowds may need
different reference treatment (RefMod, more ref stills).

## Prompt style to test (setup-style grammar)
Write each test prompt in the altoiddealer 6-field structure (the pipeline's Step-4 output):
1. `subject_definitions:` — <Subject N> physical traits + which <Picture N>/<Video 1>.
2. `summary:` — bracketed task type(s) + one paragraph.
3. `retention_analysis:` — one line per reference label; visible markers
   (fully_preserved / partially_preserved / attribute_transfer / weak_reference) and audio
   markers (fully_copy / partially_copy / reference).
4. `detailed_description:` — style line + [Shot N] blocks with camera terms + dialogue.
5. `overall_soundscape:` + 6. `non_diegetic_music:`.

Rules from the community digest to honour in every prompt:
- State what you want; never "don't show X" — the model grabs any mentioned concept.
- If a subject is silent on screen, state lip/mouth behaviour ("her lips are closed") or it
  invents speech.
- For action: name the body action and camera terms; carry motion from <Video 1>.
- Keep it lean — over-describing hurts ref2v.

## Deliverables
- `refrun.py prompt --chunk <id>` writes the 6-field prompt + graph for review (no GPU).
- Manual workflow runs produce the clips; record the winning model/LoRA/scheduler config
  back into `docs/h3_prompt_template.md` and the fni-h3-pipeline skill.

## Open questions
- Does the action ref video's own audio get reused (fully_copy) or is it replaced? The
  preprocessed refs carry the source 48kHz audio.
- Shot 1 timestamp convention: the WF instructs `00:00.000` for Shot 1; our builder currently
  only timestamps Shot 2+. Align.
