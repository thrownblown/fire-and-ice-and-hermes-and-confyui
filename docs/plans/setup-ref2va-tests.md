# Setup → ref2va assembly: test docket

*2026-10-12. Ledger for resume. The question: how to assemble raw shots into
camera **setups** and feed them to H3 ref2va, and which reference form wins.*

## Context / decision under test

`refrun.py` (REF2VA) renders a **chunk** = ~15s of *chronological* shots; its
`build_ref_video` concats the chunk's per-shot refs into one `<Video 1>`. In a
cross-cut scene that ref is a *mixed* A/B/A sequence. The new idea (AGENTS.md
"plan by setup") is to re-group shots by camera **setup** (same angle/background,
from `manifests/continuity_v2.jsonl`) so the reference carries ONE angle's
consistent look across all its recurrences, render per angle, then re-interleave
chronologically at assembly.

Two open levers from earlier: (1) ref-video length/cost — REF2VA VAE-encodes the
ENTIRE ref every render, so long setup concats are expensive; (2) whether a
stitched **plate image** can stand in for (part of) the video reference.

## Approaches (one variable each)

| id | approach | reference form | isolates |
|----|----------|----------------|----------|
| X1 | baseline chunk (current `refrun`) | mixed chronological concat (A/B/A) | control |
| X2 | setup stitched-video | concat of one setup's shots (A/A/A) | re-group by angle |
| X3 | setup plate + short video | setup plate image + ONE shot's clip | ref length/cost; plate as look source |
| X4 | per-shot + shared plate | single-shot video + setup plate image | shared plate alone, no re-group |

Pairwise: **X1 vs X2** = the grouping change; **X2 vs X3** = full-video vs
plate+short; **X1 vs X4** = shared plate without re-grouping.

## Test matrix (pilot scene S06, clean validated cross-cut)

S06 setups (v2): A=197,199,201,203,205 (5, "odd" angle); B=198,206,208;
C=200,202,204,207,209 (5, "even" angle); D=210,211,212; E=213..220.
S06-A member durations: 3.34/3.17/1.88/4.05/4.21s = 16.64s (→ capped 15s).

| T# | dir | approach | ref / input | seed | h3_s |
|----|-----|----------|-------------|------|------|
| T0011 | T0011_s06_setup-baseline | X1 | `refrun` chunk S06-c01 (197,198,199) | (chunk) | 9.4 |
| T0012 | T0012_s06_setup-stitched-video | X2 | setup S06-A concat ref | 42 | 15 |
| T0013 | T0013_s06_setup-plate-shortvideo | X3 | S06-A plate + shot 197 clip only | 42 | ~3.3 |
| T0014 | T0014_s06_setup-pershot-plate | X4 | shot 197 clip + S06-A plate image | 42 | ~3.3 |

## State ledger

| T# | state | verdict |
|----|-------|---------|
| T0011 | running on 5090 (prompt f873cc58, #106) | (Alex, after watching) |
| T0012 | queued on 5090 (prompt 39bdd146, #107) | (Alex, after watching) |
| T0013 | planned — needs plate-injection in refrun build_ref_graph | — |
| T0014 | planned — needs plate-injection in refrun build_ref_graph | — |

## Findings (session 2026-10-12)

- **`refrun.build_ref_graph` bug (FIXED):** still LoadImage nodes started at id
  137, colliding with prompt-text node 138 → `ref_image_1` wired to a STRING →
  400 `prompt_outputs_failed_validation`. Still nodes now start at 149; queue
  verified 200 OK.
- **Dialogue cap:** a 5-shot dialogue setup (S06-A: ENVOY/TARO/JAROL) exceeds
  refrun's ~200-char/clip dialogue limit → `validate_ref_prompt` warning. Setup is
  a good unit for plate/background consistency, but dialogue-heavy setups want
  per-shot rendering (X4).
- **Timing mismatch:** non-contiguous setup shots reuse per-shot dialogue
  timestamps, which are wrong against the concatenated setup ref video. Needs
  cumulative re-timing if setup-concat (X2) is pursued.

## How to resume / re-run

- Refs already built: `refs/setups/S06-*.{plate.jpg,ref.mp4}` (tool
  `tools/build_setup_refs.py`, ledger `manifests/setups.jsonl`).
- Baseline: `.venv/Scripts/python.exe refrun.py render --chunk S06-c01`.
- Setup render driver: `runs/build_setup_ref2va_test.py --setup S06-A --seed 42`
  (`--dry` builds prompt+graph with no queue).
- Endpoint: Tailscale `http://100.104.7.72:8188` (LAN 192.168.12.177 stale;
  `FNI_COMFY` unset → fullrun defaults to Tailscale).
- Pull outputs: `tools/pull_5090.py`; copy into `runs/<dir>/` and refresh
  `tools/build_testruns_data.py` so the shot-browser `?view=tests` shows them.
- Log verdicts in this file + `runs/INDEX.md` + OptMem (`core/optmem.py add`).

## Don't

- Change more than one variable per T.
- Reuse a T#### id.
- Queue T0013/T0014 before T0011/T0012 have a verdict.
- Run LM Studio concurrently with renders on the 4090 (H3 ~23 GB).