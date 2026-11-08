# Plate location ruling — 12 scenes

Every chunk attaches one scene plate. **22 of 34 scenes resolve already**, from the beat sheet's own
"Canonical location" column (`manifests/scene_locations.json`); the 12 below do not, so they are the
only chunks in the next pass that would render with **no plate**. One word per scene is enough.

## The nine G scenes — 247 chunks

These are the film's **action stretches**. Their ledger `location` field is empty and they do not appear
in the beat sheet at all, so there is nothing to match them against — the slugs currently sitting in the
table are placeholders and they attach NOTHING until ruled (a guessed plate behind a scene is worse
than none). Six plates exist that no other scene claims, and they read as made for these beats:

| plate | files on disk | claimed by |
|---|---|---|
| `frozen-landscape` | 4 | — unclaimed |
| `north-village-plain` | 5 | — unclaimed |
| `open-sky` | 5 | — unclaimed |
| `swamp` | 4 | — unclaimed |
| `wilderness` | 4 | — unclaimed |
| `ice-peak-cave` | 4 | — unclaimed |

Proposed, for you to confirm or swap (I am not attached to any of these):

| scene | chunks | placeholder |
|---|---|---|
| G01 | 15 | `frozen-landscape` |
| G02 | 40 | `north-village-plain` |
| G03 | 56 | `open-sky` |
| G04 | 18 | `swamp` |
| G05 | 10 | `wilderness` |
| G06 | 13 | `ice-peak-cave` |
| G07 | 18 | `frozen-landscape` |
| G08 | 50 | `north-village-plain` |
| G09 | 27 | `open-sky` |


## The other three — 34 chunks

These name a place but not a part of it, so the plates are genuinely ambiguous.

| scene | chunks | ledger says | plates to choose from |
|---|---|---|---|
| S15 | 5 | Fire Keep | `fire-keep-chamber` *(other scenes)*, `fire-keep-pool` *(other scenes)*, `fire-keep-ramparts` *(other scenes)*, `fire-keep-study` *(other scenes)*, `fire-keep-throne-hall` *(other scenes)* |
| S22 | 23 | Ice Peak | `ice-peak-cave` *(unclaimed)*, `ice-peak-dungeon` *(other scenes)*, `ice-peak-lava` *(other scenes)*, `ice-peak-throne-hall` *(other scenes)* |
| S24 | 6 | Fire Keep | `fire-keep-chamber` *(other scenes)*, `fire-keep-pool` *(other scenes)*, `fire-keep-ramparts` *(other scenes)*, `fire-keep-study` *(other scenes)*, `fire-keep-throne-hall` *(other scenes)* |


## If you would rather not rule now

The next pass simply skips all 12 (281 chunks) and runs the **213 that resolve** — everything else is
ready.

Images for every plate are in the SPA's **Backgrounds** tab; this table is generated from
`manifests/scene_locations.json` and `refs/backgrounds/` by `tools/build_plate_ruling_doc.py`, so it
cannot drift from what the renderer actually reads.
