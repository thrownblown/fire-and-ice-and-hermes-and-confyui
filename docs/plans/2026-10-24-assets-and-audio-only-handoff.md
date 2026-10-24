# Handoff — character sheets, location plates, and the audio-only render mode

Date: 2026-10-24. Author: Hermes (autonomous session, Alex AFK for much of it).
Next owner: whoever picks up FNI rendering next. Read `E:\FNI\AGENTS.md` and
`memory/VIEW.md` first; ground truth for rigs/services is `docs/canonical-setup.md`.

## What this session established (the headline)

**REF2VA audio-only is the mode that reaches the live-action technicolor register.**
Feeding H3 the technicolor character sheets + location plate as `<Picture>` refs while
the raw 1983 `<Video 1>` reference was still wired produced a clip that reads **flat 2D
rotoscope cel** on every sampled frame (T0015). Dropping the video reference entirely —
keeping only the source **audio** via `ref_audios.ref_audio_0` + `audio_vae` — produced a
clip that reads **live-action 80s technicolor** on the same scene (T0016). This is the
FL2VA TEST-1 pinning failure one stage up: the medium-register signal wins only at the
endpoint that actually conditions motion. It is also cheaper than full REF2VA (no video
encode).

Consequence: prefer audio-only REF2VA for Track A. Do not spend effort restyling the
video reference — remove it.

## Done (all committed and pushed; `git log --oneline` from 5142fa4 → d804080)

1. **Audio-only render path** — driver `runs/build_technicolor_audio_only.py`
   (dry by default; `--queue`, `--take`, `--seed`, `--subjects`). It builds the chunk's
   audio track itself (extract to an audio-only mp4, upload) because `LoadAudio` only
   accepts a file already in the target box's `input/`.
   - S05 (Teegra's lesson, Fire Keep bedchamber): 4 chunks, stitched →
     `runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_t04_stitched.mp4`
   - S03 (Juliana/Nekron, Ice Peak throne hall): 2 chunks, stitched →
     `runs/T0017_s03_technicolor-audio-only/S03_audioOnly_stitched.mp4`
2. **Blocking layer** — `manifests/blocking.json` (per-chunk physical blocking) injected at
   the top of `detailed_description`, plus a global "ONLY these N characters, no crowd,
   nobody walks toward the camera" constraint in the driver. Without it, and with no video
   ref, H3 invents a walk toward camera and extra people.
   - Drafting tool `tools/vlm_blocking.py` (`--sweep`, `--write`). Sweep winner:
     goldfishbowl `qwen3-vl-32b-heretic` + the `literal` system prompt. The 8B miscounts
     figures; `qwen2.5-vl-32b` hallucinated a man into a two-woman scene.
3. **Character sheets** — 17 characters (19 files; LARN and SUBHUMAN have two takes).
   12 mains already done; this session added **ENVOY, ENVOYS** (same design),
   **SUBHUMAN, SUBHUMAN CAPTAIN, SUBHUMAN LEADER**. Verified with a structured sheet
   checklist. Status doc: `refs/characters/_SHEET_STATUS.md`.
4. **Location plates** — all **21 canonical locations** verified **figure-free** with the
   32B VLM (a plate with painted/statue figures makes H3 render phantom background
   extras — that was a real bug). New tool `tools/plate_figure_check.py` (judges the
   newest take, exits non-zero so it can gate a render). The five plates that contained
   figures were regenerated clean.
5. **Two solved failure classes** (both were the prompt/plate, not the model):
   - the shared `fullrun.style_line()` says "epic practical sets and crowds" on EVERY
     location → strip it for intimate interiors or H3 adds a crowd;
   - naming an object you want ABSENT in a positive prompt BACKFIRES ("no portraits, no
     statues" produced three of each) — describe the room you want, positively.
6. **Test-runs SPA tab** — `runs/testruns-data.js` rebuilt by `tools/build_testruns_data.py`;
   the tab now lists **15 runs / 113 clips** including T0015–T0017. Fixed a real bug: the
   builder globbed `T000*`, silently skipping every run from T0010 on.
7. **Bugs fixed** — `LoadAudio` node-id collision (hardcoded 152 collided with
   `build_ref_graph`'s `LoadImage` ids from 149; 400'd on any chunk with 4+ ref images);
   truncated-mp4 races (new `tools/pull_verified.py`: fetch + ffprobe integrity + retry);
   `plate_path()` now prefers the highest take.

## Gaps / open questions

- **The S05 4×6 seed sweep is rendered but NOT scored.** 24 clips in
  `runs/T0016_.../output/seedhunt/` (seeds 111…66666666, 4 chunks). No winner picked per
  chunk. Scoring plan: per-chunk contact sheet of the 6 seeds × 3 timepoints, 32B VLM for
  "extras? correct blocking? walk-in?", keep the best.
- **S05 still has a brief mid-clip stand** (t=6 s) where the characters should stay
  lounging. The blocking could be pushed harder ("seated the entire time; never stands").
- **S05-c01 straddles a scene boundary.** Its shot 188 is a different scene (three hooded
  figures on a balcony, pre-dialogue). The chunk should be re-cut before trusting its
  blocking draft — this is unfixed.
- **S03-c01 carries a TEEGRA mis-stamp** in `fullrun/chunks.jsonl` (she isn't in S03).
  Worked around with `--subjects JULIANA,NEKRON`; the ledger itself is still wrong.
- **9 roster names have no reference material and no sheet**: ELDER, GUARDS, NARRATOR,
  OTWA?, RIDERS, SUBHUMANS, VILLAGE CHIEF, VILLAGE ELDER. NARRATOR is voice-only; the rest
  are 1–2-line group roles. Making sheets needs source frames mined from `stills/full/`
  first (VILLAGE CHIEF/ELDER → S02; GUARDS/RIDERS → S21; SUBHUMANS → S02/S07/S14).
- **The subhuman design is provisional.** `refs/characters/SUBHUMAN/note.txt` records it as
  "NOT APPROVED — needs a human eye". The three subhuman sheets fix a look by assumption;
  redo if a different design is chosen (`shot_00119`, the hulk with the tooth necklace and
  cigar, remains an unsettled candidate).
- **SUBHUMAN sheets return 3 full-body views, not 4** (both takes). Qwen-2.1 would hold
  the fourth.
- **`.gitignore` excludes `*.html`**, so `browser/index.html` (the SPA) is untracked while
  its data file is tracked. Needs an exception if the markup should be versioned.
- **The audio-only driver writes every scene's prompts into the one T0016 dir**
  (`RUN_DIR` is hard-coded). Cosmetic; give it a per-scene run dir when convenient.
- The remaining ~20 canonical locations' plates have **no approved human verdict** — they
  are figure-free and VLM-scored 4–5/5, but Alex has not watched them.

## Next step (recommended, in order)

1. **Score the seed sweep and pick a winner per S05 chunk** (cheap, already on disk) — this
   turns 24 unfiltered takes into one chosen S05 scene.
2. **Re-cut S05-c01** to drop the balcony shot, then re-author its blocking.
3. **Extend audio-only to the next scenes** — author blocking per chunk with
   `tools/vlm_blocking.py` (32B/literal), correct the cast clause by hand, render, stitch.
   S06 (the abduction cross-cut) and the rest of S03 are the natural next batch.
4. Only then consider more character sheets — the nine remaining names need mined reference
   frames first, and that is a separate task.

## How to run things

```
.venv/Scripts/python.exe runs/build_technicolor_audio_only.py --chunk S05-c01 \
    [--subjects JULIANA,NEKRON] [--seed N] [--take N] --queue
.venv/Scripts/python.exe tools/vlm_blocking.py --scene S06 --model qwen3-vl-32b-heretic:latest --sys literal
.venv/Scripts/python.exe tools/plate_figure_check.py            # gates on any plate with figures
.venv/Scripts/python.exe tools/gen_char_sheet.py --char NAME --queue
.venv/Scripts/python.exe tools/gen_location_plates.py --loc SLUG --take N --queue
.venv/Scripts/python.exe tools/pull_verified.py --list <file> --dest <dir>
.venv/Scripts/python.exe tools/build_testruns_data.py           # then open browser/index.html?view=tests
```

Rigs: H3 renders → the 5090 (Tailscale <TOMBSTONE_TS_IP>:8188). Krea2 stills → the 5090 too.
VLM QC → goldfishbowl `qwen3-vl-32b-heretic` (`http://<GOLDFISHBOWL_TS_IP>:11434`). Never render
H3 on the 4090; serialize LM Studio vs ComfyUI on the 4090's single GPU.
