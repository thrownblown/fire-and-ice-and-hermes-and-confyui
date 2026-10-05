# Scene 10 ledger — Roliel's cottage — Design

**Date:** 2026-09-21
**Status:** approved scope, design written, not yet planned
**Authority:** superpowers brainstorm. No implementation in this file.

## Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | First slice | Scene 10, Roliel's cottage. Mid-film, interior, three bodies (Teegra, Roliel, Otwa). Not credits. Not a fight. |
| 2 | How the span is found | Location noun + trait cluster. Not a guessed minute. Film is ~82 min, 1308 shots. |
| 3 | Naming | VLM never names characters. Clusters get temporary ids. User maps id to roster once. |
| 4 | Passes | Three separate calls per shot sample: people, location, creatures. Already in `core/vlm_correlate.py`. |
| 5 | Chunking | Existing `group_shots`. Feed it normalized location + cluster ids. Cap 3. Split on place, person-set, or span past ~15s. |
| 6 | H3 | Out of this build. Prompts, if written, follow the six-section vendor spec. No render from this pipeline. |
| 7 | Hardware | VLM stays on the 4090 (this box, LM Studio :1234). 5090 is manual H3. Do not start ComfyUI here. |

## Why not the other approaches

Hand-labeling this scene tests the chunker and teaches nothing about the film.
Asking the 8B to name characters per still already failed (invented archetypes, merged figures).

## Architecture

```
stills for candidate shots
        |
        v
three VLM passes (people / location / creatures)
        |
        v
normalizer  -->  stable trait tokens + location noun
        |
        v
ledger (one row per shot sample)
        |
        +--> cluster recurring bodies  -->  person_A, person_B, creature_C
        |
        v
user name map (person_A = Teegra, ...)
        |
        v
group_shots  -->  2-3 shot chunks
```

Candidate shots are a window around the middle of the film, wide enough to contain the cottage and its edges. The ledger decides which shots belong to the scene. The window is only a bound so the first run is not 1308 shots.

## Components

- `core/vlm_correlate.py` — unchanged callers: `describe_people`, `describe_location`, `describe_creatures`. Retry and empty-list cleanup stay.
- `core/ledger.py` — new. Normalize one VLM payload into tokens. No I/O.
- `core/cluster.py` — new. Group shot-level person observations that share a trait signature. Emit cluster ids. Mark unreliable shots and exclude them from clustering, not from the timeline.
- `core/scene_slice.py` — new. Given ledger rows, return the ordered shot ids that belong to the cottage slice (location family + at least one of the approved clusters).
- `core/chunker.py` — existing. Caller builds `{shot_id: {location, characters}}` from cluster ids (or approved names after the map). Do not change grouping rules in this build.
- `docs/character_descriptions.md` — curation input. Not parsed as code. The name map is a small JSON file the user edits.

## Data

Ledger row (one per sampled shot):

```
shot_id, pts, people_raw, location_raw, creatures_raw,
location_token, people_tokens, creature_tokens,
people_unreliable, error
```

Cluster:

```
cluster_id, kind (person|creature), signature tokens, shot_ids, example still
```

Name map:

```
cluster_id -> roster name or "unknown"
```

Unreliable: `count` disagrees with distinct descriptions, or every person entry is identical. Those rows keep their location token. They do not vote in a cluster.

## Data flow for the first run

1. Pick a bounded shot window (middle third). Do not run the whole film.
2. For each shot, call the three VLM functions on up to 3 stills.
3. Normalize. Write `manifests/scene10_ledger.jsonl`.
4. Cluster. Write `manifests/scene10_clusters.json`.
5. Stop. User maps names. No chunker run until that map exists.
6. After the map: `group_shots` on the slice. Write `manifests/scene10_chunks.json`.

Step 5 is a hard stop. A wrong name map chunked automatically is worse than no chunks.

## Error handling

- HTTP 400/5xx: existing 3-attempt retry, then `error` set, row kept, no invented people.
- JSON parse failure: same. Row kept with `error`.
- Empty people and empty location: valid. Not an error. Credits-like frames fall out of the slice.
- Unreliable people: flagged, excluded from cluster votes.

## Testing

- Normalizer and cluster are pure. Tests use fixture JSON, no VLM, no network.
- Chunker tests already exist. Add one test that builds labels from cluster ids and checks a location change splits.
- The VLM run is a script, not a unit test. It is not part of `pytest`.

## Out of scope

Rendering, LoRA choice, H3 variant swap, ASR, speaker names inside dialogue, full-film ledger, starting ComfyUI on this machine.
