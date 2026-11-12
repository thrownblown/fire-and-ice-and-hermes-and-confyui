# Fire & Ice — remake pipeline

A local-only AI remake of Ralph Bakshi's *Fire & Ice* (1983), rendered with MiniMax H3 in ComfyUI.

The media never leaves the rigs. This repo tracks the **work** — shot lists, chunk manifests, prompts,
decisions, ledgers — not the film: the source master, and every video, still and audio stem derived
from it, are gitignored. That is what lets this repository be public without publishing anyone's film.

Three rigs; ground truth for all of it is `docs/canonical-setup.md`.

| rig | hardware | role |
| --- | --- | --- |
| `mh370` | Windows, RTX 4090 | dev box: ComfyUI, Krea/plate stills, LM Studio VLMs |
| `tombstone` | Linux, RTX 5090 | render box: H3 ref2va |
| `goldfishbowl` | 2× Radeon R9700, Unsloth Studio | model server (32B VLM, embeddings) |

The rigs reach each other over Tailscale. Addresses in the tracked docs are placeholders; the real
ones live in the gitignored `docs/rig-addresses.local.md`.

## Source

Bring your own rip — a disc you own. Nothing here downloads one, and nothing here names one: the
scripts resolve the master from `$FNI_MASTER`, else from `docs/source-master.local.json`
(gitignored), and fail loudly if neither is set. The master is never modified.

## Pipeline

| Script | Stage | Notes |
| --- | --- | --- |
| `pipeline/cut_detect.py` | 1 | hashes the master, PySceneDetect ContentDetector (thr 27, min_len 12) → `shots.jsonl`, `master.json` |
| `pipeline/chop.py` | 1b | frame-exact slice per shot; re-encode CRF 14 — the master's ~10.4 s GOP defeats stream copy |
| `pipeline/keyframes.py` | 1c | first/median/last still per shot + per-shot audio stems; optional full-master audio decode |
| `pipeline/run_overnight.sh` | — | full-film chop + keyframes, resumable |
| `core/chunker.py` | 2 | merges shots into render chunks sized to H3's frame grid → `fullrun/chunks.jsonl` |
| `pipeline/fullrun.py` | 3 | FL2VA pipeline (3-field prompt grammar) |
| `pipeline/refrun.py` | 3 | REF2VA successor (6-field grammar), reference-video conditioned |
| `runs/yolo_full_movie.py` | 4 | queues every chunk through the audio-led ref2va driver; resumable via `runs/yolo_state.json` |
| `runs/assemble_movie.py` | 5 | stitches takes into a cut in source-timecode order |
| `tools/serve_media.py` | — | range-capable static server, so a stitched cut scrubs in a browser |

`cut_detect`/`chop`/`keyframes` accept `--offset`/`--minutes` and `--tag`, and re-running is safe:
existing clips, stills and stems are skipped.

Entry-point scripts live in `pipeline/`, the shot browser in `browser/`, throwaway probes in `probes/`,
superseded directories in `archive/`.

## Assembly

`runs/assemble_movie.py` orders chunks by `src_start` — the chunk list is grouped by scene, so the
source timestamp is what gives film order, and the S and G scene namespaces interleave into one cut.
Per chunk it takes the highest available take (later takes follow prompt fixes); a chunk with no take
falls back to the older pass in `fullrun/output/`. Every fallback is recorded as `old_fill` in
`fullrun/stitched/assembly_manifest.jsonl` rather than passed off as a take, and every segment is
normalised to one profile before concatenation.

Watch a cut with `tools/serve_media.py --root fullrun/stitched --port 8646`. Plain `http.server`
answers a Range request with 200 and sends no `Accept-Ranges`, so a browser cannot seek a long video;
this one serves 206 with `Content-Range`.

## Data

    shots.jsonl            1308 shots. PTS integer-exact: start_pts == start_frame * 1001
    master.json            hashed source record + ffprobe facts + detection params (neutral id)
    fullrun/chunks.jsonl   494 render chunks (2.65 shots/chunk), 15 s cap
    stills/full/           3924 stills (first/median/last per shot)
    audio/                 81-min master bed + 1308 per-shot stems
    manifests/             clip + keyframe + character + continuity ledgers
    fullrun/stitched/      assembly manifest (the media itself is gitignored)

## Reference material

    docs/        design docs, H3 prompt guides, canonical-setup, plans/
    archive/     superseded dirs (test_runs/, testing/, chunks/, s03/)
    browser/     shot browser (data rebuilt from the manifests)
    corpus/      LOCAL ONLY, untracked: scraped reference art and saved pages, not in this repo

## Known constraints

- **H3's frame grid is `17k+5` at 24 fps; the qualified minimum is 124 frames (5.17 s).** 84% of the
  film's shots (1093/1308) fall short of that on their own, which is why shots are merged into
  multi-shot chunks: across the 494 chunks, 16% (80) are still under 124 frames. Chunking is the
  answer to what an earlier revision of this file called the largest open design question.
- **Source is 1920x1072, not 1080.** Resolve the true display aspect before treating it as 16:9.
- **Blank-still threshold is 20 KB**, calibrated from title frames (13–15 KB): 8 flags out of 3924,
  all titles/credits/fades, no false positives on dark content. Still an unmeasured default.
- Clips are CRF 14 derivatives, not archival copies. The master is untouched.
