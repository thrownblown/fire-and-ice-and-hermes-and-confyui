# AGENTS.md — Fire & Ice (FNI) remake pipeline

Entry point for ANY agent (Hermes, Claude Code, Codex, other) working in `E:\FNI`.
Read this first, then `memory/VIEW.md`. Keep this file current when conventions change.

## What this is

A local-only AI film remake of Ralph Bakshi's **Fire & Ice (1983)** using **MiniMax H3**
(ComfyUI) for video+audio generation. Source master is hashed and never modified; all
video/still/audio derivatives are gitignored — the repo tracks the *work* (shot lists,
manifests, ASR, prompts, run metadata), not the media. Design authority:
`docs/README (3).md` → `docs/IMPLEMENTATION_PLAN (1).md`.

## START HERE (mandatory)

1. **`memory/VIEW.md`** — whole project history, ~16 KB, one line per event, `id+span` addressed.
   Open a line: `python core/optmem.py zoom <id> <span>` (zoom again to reach the original).
2. **This file** for conventions and layout.
3. Load the skill **`fni-h3-pipeline`** (in the Hermes profile, not this repo) before touching
   H3 prompts or debugging renders.
4. Authoritative detail still lives where it belongs: ledgers, `docs/*.md`, the skill.

## Environment

- Root `E:\FNI`. Host is **Windows**; the shell is **git-bash/MSYS** (POSIX syntax). Native
  tools (git, rg, python) do NOT translate `/c/...` paths — pass `C:/...`/`E:/...` style.
- **Venv: `E:\FNI\.venv`** — Python 3.11, uv-managed, **no pip**. Install with
  `VIRTUAL_ENV=E:/FNI/.venv uv pip install <pkg>`. Run scripts as
  `.venv/Scripts/python.exe <script>`. System python is 3.14 (too new for the wheels) — never
  use it for FNI.
- **Two rigs.** RTX **5090** = dedicated H3 render box (only thing running there). RTX **4090**
  Windows = general-purpose (LM Studio, dev). **Never run LM Studio and an H3 render on the
  same GPU** (H3 stack ~23 GB). ComfyUI: Tailscale `100.104.7.72:8188`, LAN `192.168.12.177:8188`
  (env `FNI_COMFY`, default now Tailscale). `/history` wipes on reboot — recover outputs with
  `tools/pull_5090.py`. Windows box IPv6 is broken: force IPv4 (`curl -4`).
- LM Studio (`127.0.0.1:1234/v1`) roles: vision = `qwen3-vl-8b`; general small = mistral-7b;
  prompt-craft = sulphur_2. Subagents use LM Studio via `delegation.provider`; the 27B models are
  crash-prone and qwq-32b's 40k context is below Hermes's 64k floor.

## Core concept: SETUPS (read before planning any render)

A **setup** = one camera position/angle shared by 1+ shots in a scene. It is the unit the
pipeline prompts by: shots that cut back and forth (cross-cut) share a setup, get prompted
together with ONE master background plate, then are split apart at assembly. **Plan by setup,
never by the film's chronology.** Gemini/Alex ruling (VIEW line i=31): identify setups, chain
them, render out of order, reassemble chronologically by shot id (the timeline TSV keeps sync).

- Signature = `location + framing + angle`; framing ∈ {XWS,WS,FS,MS,MCU,CU,ECU}, angle ∈
  {eye-level, high-angle, low-angle, over-the-shoulder, POV, aerial}.
- `core/setups_v2.py` (VLM-labels each shot's first frame) is CORRECT. `core/continuity.py`
  (v1, grayscale SSIM on the first frame only) fragments dialogue/action scenes to ~1 setup per
  shot (S07: 30 shots → 29 setups) — v1 output is `manifests/continuity.jsonl`; v2
  (`manifests/continuity_v2.jsonl`) has only a PILOT run (S02,S03,S06) so far.
- Consumers: `tools/build_setups_data.py` → `setups-data.js` (shot-browser "Setups" tab).

## Pipeline

- **`fullrun.py`** = main FL2VA pipeline (plan/caption/prompt/render/collect/recover). **Archived
  as tag `fl2va-baseline`** — the old full run is versioned there. Its 3-field prompt grammar is
  `integrated_multimodal_description / overall_soundscape / non_diegetic_music`.
- **`refrun.py`** = the REF2VA successor (reference-VIDEO conditioned). Emits the SIX-field
  grammar: `subject_definitions / summary / retention_analysis / detailed_description /
  overall_soundscape / non_diegetic_music`. Imports `fullrun` for loaders/roster. Commands:
  `refrun.py prompt --chunk S05-c04` (dry-run, no GPU) and `refrun.py render ...` (upload + queue).
- Stages: `cut_detect.py` → `chop.py` → `keyframes.py` (1–1c, resumable);
  `stage1_inventory` → `stage2_characters`/`stage2b_names` → `stage3_composition` →
  `stage4_alignment` → `stage5_chunks` → `stage6_h3_prompts` → `stage7_queue`. Shared library
  in `core/` (optmem, chunker, continuity, setups_v2, asr, align, …). Dialogue lives in
  `script/dialogue-timeline.tsv` (id, speaker, text, start/end PTS).
- Grammar mode MUST match the model mode (FL2VA ⇄ 3-field, REF2VA ⇄ 6-field). Never drift.
- `validate_prompt()` (fullrun.py) checks the 3-field contract; `refrun.py` has
  `validate_ref_prompt()` for the 6-field contract. Both are non-fatal advisory checks.

## Data layout

    shots.jsonl            1308 shots; PTS integer-exact (start_pts == start_frame * 1001)
    fullrun/chunks.jsonl   494 render chunks (15 s cap) — the render unit; each has scene,
                           shots[], shot_nums[], speakers[], stamped_names[], line_ids[],
                           h3_seconds, h3_frames, seed, motion[], shot_type[], angle[]
    refs/*.mp4             1308 preprocessed REFERENCE clips, 1280x720 @ 24 fps (preprocess_ref.py)
    refs/refs_manifest.json  provenance for the above
    stills/full/           3924 stills (first/median/last per shot, 3x1308)
    audio/                 master_audio_48k_stereo.wav (81 min), stems/full/*.wav
    manifests/             keyframe + character_pass + character_names + continuity ledgers
    fullrun/               chunks.jsonl, renders.jsonl, qc-results.jsonl, stitched/
    runs/                  test runs T0001.. + build_*.py drivers + INDEX.md
    library/char/sheet-runs/  character sheet generations + seeds.tsv
    docs/                  design docs, H3 prompt guides, plans/, thread digests
    memory/                OptMem: log/ (truth), tree.jsonl, VIEW.md (cache), optmem.py CLI
    explore/               mined external repos (konte, OpenCineAgent)

## Working conventions

- **Do not duplicate ledgers.** Memory entries and docs POINT at machine ledgers
  (`fullrun/renders.jsonl`, `manifests/*.jsonl`, `seeds.tsv`) by name/count; never copy rows.
- **Ledgers by kind:** `memory/log/` = rulings/verdicts/decisions (durable meaning);
  `docs/*.md` = settled plans/specs (a decision frozen into prose); `manifests/*.jsonl` =
  machine state.
- **Write the artifact, not a description of it.** Success = a downloaded, non-empty artifact —
  never queue state.
- **Verify copies by comparing source and destination counts** — never trust the copy
  command's own glob (this bit us once; a glob silently dropped T0004's second take).
- Never make anything look further along than it was.

## On finishing work: append to OptMem

```
python core/optmem.py add --kind user --text "Alex ruled: ..."      # his words, near-verbatim
python core/optmem.py add --kind work --text "<session report>"     # what changed on disk, what failed and why
python core/optmem.py pump     # compress new messages into the tree (LM Studio, ~1 min)
python core/optmem.py view     # regenerate memory/VIEW.md
```

Priority: Alex's own words near-verbatim → lasting effects (files/counts/seeds/verdicts) →
findings → tool noise last (described, not copied). Short-lived agents may append (`add`) but
should NOT `pump` — leave that to the long-lived project chat. `add` is lock-serialized.

## Known constraints / open questions

- **H3 frame grid is `17k+5` at 24 fps, qualified minimum 124 frames (5.17 s).** 83.6% of shots
  (1093/1308) are shorter; median shot = 2.419 s = 58 frames. Biggest open design question:
  generate-long-and-keep-short / merge adjacent shots / qualify a shorter profile.
- Source is 1920x1072, not 1080 — resolve true display aspect before treating as 16:9.
- Turbo/few-step LoRAs **deep-fry the audio**; do not combine them with Spectrum/SOL attention.
  Community: don't run the 4-step LoRA at strength 1.0 for ref2video (full steps, or ~0.4).
- Seed instability / deep-fried re-rolls → **restart ComfyUI** first.
- S10 is the only scene with no renders (separate `run_scene10_ledger.py` approach).
- QC: black/frozen motion + near-silent audio checks are specified but **not yet absorbed**.
