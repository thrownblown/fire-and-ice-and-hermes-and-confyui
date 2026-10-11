# Test runs

| id | scope | method | verdict |
|---|---|---|---|
| T0001 | S03 | ref2v, original stills | decent — Alex, 2026-09-27 |
| T0002 | S03 | ref2v, same refs and seed, split at action beats | pretty good — Alex, 2026-09-28 |
| T0003 | S03 | fl2va (first/last source stills), same chunks and seed as T0002 | (Alex, after watching) |
| T0004 | S03 | fl2va motion-path variant (source frame deltas), 2 takes | (Alex, after watching) |
| T0005 | S03 | fl2va action variant | (Alex, after watching) |
| T0008 | S03 | original master audio over the T0001 video (audio plan A baseline) | audition pending |
| T0009 | S02 | continuity-packed segments (SSIM chains/setups) vs chronological | renders done — compare S02_continuity_audioA vs S02_chronological_audioA |

Browsable in the shot browser: `shot-browser.html?view=tests` — data generated
by `tools/build_testruns_data.py`, re-run it after copying new renders in.
Clips: `runs/<id>_*/output/`, `runs/testruns/` (copies from the 5090 drive),
plus `runs/T0008_*/` and `runs/T0009_*/` audio overlays.
