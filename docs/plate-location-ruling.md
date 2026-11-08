# Plate location ruling — 0 scenes

Every chunk attaches one scene plate. **22 of 34 scenes resolve already**, from the beat sheet's own
"Canonical location" column (`manifests/scene_locations.json`); the 0 below do not, so they are the
only chunks in the next pass that would render with **no plate**. One word per scene is enough.

## The nine G scenes — 0 chunks

These are the film's **action stretches**. Their ledger `location` field is empty and they do not appear
in the beat sheet at all, so there is nothing to match them against — the slugs currently sitting in the
table are placeholders and they attach NOTHING until ruled (a guessed plate behind a scene is worse
than none). Six plates exist that no other scene claims, and they read as made for these beats:

| plate | files on disk | claimed by |
|---|---|---|
| `frozen-landscape` | 3 | — unclaimed |
| `north-village-plain` | 3 | — unclaimed |
| `open-sky` | 3 | — unclaimed |
| `swamp` | 3 | — unclaimed |
| `wilderness` | 3 | — unclaimed |
| `ice-peak-cave` | 3 | — unclaimed |

Proposed, for you to confirm or swap (I am not attached to any of these):

| scene | chunks | placeholder |
|---|---|---|



## The other three — 0 chunks

These name a place but not a part of it, so the plates are genuinely ambiguous.

| scene | chunks | ledger says | plates to choose from |
|---|---|---|---|



## If you would rather not rule now

The next pass simply skips all 0 (0 chunks) and runs the **213 that resolve** — everything else is
ready.

Images for every plate are in the SPA's **Backgrounds** tab; this table is generated from
`manifests/scene_locations.json` and `refs/backgrounds/` by `tools/build_plate_ruling_doc.py`, so it
cannot drift from what the renderer actually reads.
