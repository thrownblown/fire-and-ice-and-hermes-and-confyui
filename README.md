# Fire & Ice — Project Folder

Local-only H3 remake pipeline. Single RTX 5090, Ubuntu/Linux target.
Design authority: `docs/README (3).md` → `docs/IMPLEMENTATION_PLAN (1).md`.

## Source

Bring your own rip — a DVD/Blu-ray or a file from your own disc. Drop it
in this folder and point the scripts at it; nothing here downloads one.
The source master is never modified and is gitignored, as is every video,
still, and audio stem derived from it. What the repo tracks is the work:
shot lists, manifests, ASR, prompts, and per-run metadata.

    Fire.And.Ice.1983.1080p.BluRay.x264-[YTS.AM].mp4   the source master, never modified
    sha256 2d6195fbb16c9ab34d3f8eff8709a349bcdccdd39f07391fda721f1827d5cc93

## Pipeline scripts

| Script | Stage | Notes |
| --- | --- | --- |
| `cut_detect.py` | 1 | Hashes master, PySceneDetect ContentDetector (thr 27, min_len 12) → `shots.jsonl`, `master.json` |
| `chop.py` | 1b | Frame-exact slice per shot. Re-encode CRF 14 — the master's ~10.4s GOP defeats stream copy |
| `keyframes.py` | 1c | first/median/last stills per shot + per-shot audio stems; optional full-master audio decode |
| `run_overnight.sh` | — | Full-film chop + keyframes, resumable |

All three accept `--offset`/`--minutes` (minutes from film start) and `--tag`.
Re-running is safe: existing clips/stills/stems are skipped.

## Data

    shots.jsonl          1308 shots. PTS is integer-exact: start_pts == start_frame * 1001
    master.json          hashed source record + ffprobe facts + detection params

    clips/full/          1308 clips   6.6 GB   whole film
    clips/m000_010/       111 clips             first 10 min
    clips/m036_046/       111 clips             mid-film sample
    stills/full/         3924 stills  826 MB    3 per shot (first/median/last)
    stills/m036_046/      333 stills

    audio/master_audio_48k_stereo.wav   940 MB   continuous 81-min bed, pcm_s16le 48k stereo
    audio/stems/full/      1308 wav    900 MB   per-shot stems
    audio/stems/m036_046/   111 wav

    manifests/clips/       clip manifests (per-shot provenance + verified frame counts)
    manifests/             keyframe manifests (sample indices, blank flags, stem map)

## Reference material

    docs/          v0.3 design docs, H3 prompt guides, core schema, synthetic fixture
    corpus/        downloaded Frazetta/Bakshi reference images + saved web page
    test_runs/     superseded logs and outputs from the first failed extraction attempts

## Known constraints

- **H3 frame grid is `17k+5` at 24fps, qualified minimum 124 frames (5.17s).**
  83.6% of shots (1093/1308) are shorter than this. Median shot is 2.419s = 58 frames.
  Unresolved: generate-long-and-keep-short, merge adjacent shots, or qualify a
  shorter profile. This is the largest open design question.
- **Source is 1920x1072, not 1920x1080.** Resolve true display aspect before
  treating it as 16:9.
- **Blank-still threshold is 20 KB**, calibrated from title frames (13-15 KB).
  Validated on the full film: 8 flags out of 3924, all titles/credits/fades,
  no false positives on dark content. Still an unmeasured default.
- Clips are CRF 14 derivatives, not archival copies. The master is untouched.