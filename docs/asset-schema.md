# Fire & Ice — Wardrobe & Prop Asset Schema

Canonical data model for storing, versioning, and reusing a character's wardrobe and
props across shots. Directory-per-asset + one manifest per folder, no database.
Anything that can read files can consume it (image-gen pipes, edit tooling, the shot
browser). This spec is normative for NEW work; it does not yet retrofit the existing
`refs/characters/` + `library/char/sheet-runs/` output (see "Migration note" at the end).

## 1. Entities and identifiers

Four entities: **Character**, **Wardrobe**, **Prop**, **Shot**. All ids are
lowercase-ish, ASCII-slug, globally unique, stable (never reused after deprecation).

| Entity   | id form                                      | example                |
|----------|----------------------------------------------|------------------------|
| Character| `character_id` = roster slug                | `teegra`, `darkwolf`   |
| Wardrobe | `garment_id` = `<character_id>.<slot>.<slug>`| `teegra.top.halter`    |
| Prop     | `prop_id` = `<category>.<slug>`             | `melee.obsidian_dagger`|
| Shot     | `shot_id` = existing `shot:NNNNN` key       | `shot:00023`           |

Rationale: namespacing garment ids under their owning character makes collisions
impossible and makes "every garment belongs to one character" a structural invariant.
Props are global (two characters can carry the same sword).

### Canonical slots (Wardrobe)

`top`, `bottom`, `outerwear`, `shoes`, `accessory`. A single full-body garment (a robe,
a one-piece) is `outerwear` with `covers: ["full"]`; a loincloth is `bottom`. Multiple
accessories that read as one outfit item (arm bands + necklace) may be split or grouped
into one `accessory` garment at the curator's discretion — group only when they always
appear together and share a color/material.

### Status lifecycle (every entity and every reference)

`draft` -> `approved` -> (optionally) `deprecated`. Only `approved` garments/props may
be referenced by a shot's generation prompt. `deprecated` means "do not reuse"; the id
is never deleted or reassigned.

## 2. Directory layout

```
assets/
  characters/
    <character_id>/
      manifest.yml                      # Character entity (section 3)
      refs/
        face.front.png                  # canonical face refs (angles = section 6)
        face.profile.png
        body.front.png
        body.back.png
      wardrobe/
        <garment_id>/
          manifest.yml                  # Wardrobe entity (section 4)
          refs/
            front.png
            back.png
            side.png
            detail.<label>.png          # fasteners / texture / embroidery crops
      traits.md                         # free-form curator notes (replaces traits.txt)
  props/
    <prop_id>/
      manifest.yml                      # Prop entity (section 5)
      refs/
        <angle>.png
        detail.<label>.png
      placement.md                      # optional scale/placement notes as prose
  shots/
    <shot_id>.yml                       # Shot entity (section 7), keyed to shots.jsonl
```

Rules:

- One folder per asset, one `manifest.yml` per folder. The folder name is the asset id.
- `refs/` holds reference images only. Angles other than the fixed set (`front`, `back`,
  `side`, `profile`, `top`, `detail.<label>`) are discouraged; new angles must be added
  to the allowed list before use.
- `version` bumps inside the manifest (new folder not required), but `deprecated`
  versions keep their files so historical shots stay reproducible.
- Images are gitignored like every other media derivative; only manifests are tracked.

## 3. Character entity — `manifest.yml`

```yaml
schema: fni.asset/character/v1
character_id: teegra
name: Teegra
status: approved                       # draft | approved | deprecated
version: 3

canonical_refs:                        # the "this is Teegra" identity set
  face:
    front: refs/face.front.png
    profile: refs/face.profile.png
  body:
    front: refs/body.front.png
    back: refs/body.back.png

distinguishing_traits:
  - very long dark hair, usually loose
  - pale skin
  - slender athletic build

wardrobe_ids:                          # garments owned by this character == subfolders
  - teegra.top.halter
  - teegra.bottom.skirt
  - teegra.shoes.sandals

lineage:                               # audit: where these refs came from
  source_shot: shot:00873
  derived: vlm + manual curation
```

`canonical_refs` are the set an identity-check or face-retention run must match against;
`wardrobe_ids` list which garment folders belong to this character (must equal the
folders present under `wardrobe/`).

## 4. Wardrobe entity — `manifest.yml`

```yaml
schema: fni.asset/garment/v1
garment_id: teegra.top.halter
character_id: teegra
name: Teegra's halter top
slot: top                             # top | bottom | outerwear | shoes | accessory
version: 2
status: approved                      # draft | approved | deprecated

refs:                                 # reference-image convention, section 6
  front: refs/front.png
  back: refs/back.png
  side: refs/side.png
  detail.embroidery: refs/detail.embroidery.png

materials:
  color:
    primary: [166, 133, 196]          # approx HTML/RGB — VLM-reported, see section 6
    primary_name: "pale purple"
  material: "woven cloth, matte"

notes: |
  Sleeveless, ties at the neck. Purple, NOT a fur bikini — earlier notes were wrong.
```

`color` carries both the sampled RGB triple and a human name; VLM-reported values
outrank hand-typed names (see section 6). `refs` keys are the fixed angle names.

## 5. Prop entity — `manifest.yml`

```yaml
schema: fni.asset/prop/v1
prop_id: melee.obsidian_dagger
name: Obsidian dagger
category: melee                       # melee | ranged | mount | set-dressing | wearable
version: 1
status: approved

refs:
  front: refs/front.png
  side: refs/side.png
  detail.blade: refs/detail.blade.png

scale:                                # placement/scale so it reads at the right size
  relative_to: "adult male hand"
  approx_length_cm: 28

notes: |
  Black glass blade, simple bone hilt. Carried at the hip, edge forward.
```

`scale` is advisory (the generator reads prose/keys, not any unit system); keep
`relative_to` human-readable so a prompt assembler can drop it straight into a scene note.

## 6. Approved-reference rules (normative)

A reference image may be `approved` only when ALL hold:

1. **Resolution** — short edge >= 1024 px (source is 1920x1072; do not upscale-then-approve).
2. **Isolation** — subject alone on a neutral background (plain white or 18% gray);
   no other actor, prop, or background element intersects the subject's silhouette.
3. **Lighting** — even frontal key, no hard edge shadows across identity features
   (face) or across the garment's defining details. One consistent light setup across
   the whole angle set.
4. **Completeness** — a garment must have at least `front` + `back`; a character at
   least `face.front` + `body.front`; a prop at least `front`. Gaps are `draft`.
5. **Color accuracy** — color in the manifest must come from a VLM report on the
   reference, not from memory/notes. Note this in `notes` when the VLM value conflicts
   with an older hand-typed value and state which won.

Anything failing 1–5 stays `draft` and must not appear in a shot's `wardrobe_ids` /
`prop_ids`.

## 7. Shot entity — `assets/shots/<shot_id>.yml`

Augments (does not duplicate) `shots.jsonl` and the timeline. Keys to the existing
`shot_id`; records what got composed into the generation and every edit pass applied.

```yaml
schema: fni.asset/shot/v1
shot_id: shot:00023
characters:
  - character_id: larn
    wardrobe_ids: [larn.bottom.loincloth, larn.accessory.belt, larn.shoes.boots]
    prop_ids: [melee.sword]
base_generation:
  image: paths resolve at render time            # master plate / ref frame
  plate: null                                    # set when a shared background plate exists
edit_passes:
  - pass: restyle
    model: qwen-image-edit
    note: "color+style pass on the assembled still"
status: draft                                     # draft | approved
```

Only `approved` garment/prop ids are permitted in `characters`. `edit_passes` is an
append-only log; removal is expressed by adding a `revert` pass, never by editing history.

## 8. Worked example — fully populated character (Teegra)

Directory:

```
assets/characters/teegra/
  manifest.yml
  refs/face.front.png  refs/face.profile.png  refs/body.front.png  refs/body.back.png
  wardrobe/teegra.top.halter/manifest.yml      (+ front.png, back.png, side.png, detail.embroidery.png)
  wardrobe/teegra.bottom.skirt/manifest.yml
  wardrobe/teegra.shoes.sandals/manifest.yml
  traits.md
```

`teegra` character record as JSON (same entity, machine-readable form):

```json
{
  "schema": "fni.asset/character/v1",
  "character_id": "teegra",
  "name": "Teegra",
  "status": "approved",
  "version": 3,
  "canonical_refs": {
    "face": { "front": "refs/face.front.png", "profile": "refs/face.profile.png" },
    "body": { "front": "refs/body.front.png", "back": "refs/body.back.png" }
  },
  "distinguishing_traits": [
    "very long dark hair, usually loose",
    "pale skin",
    "slender athletic build"
  ],
  "wardrobe_ids": [
    "teegra.top.halter",
    "teegra.bottom.skirt",
    "teegra.shoes.sandals"
  ],
  "lineage": { "source_shot": "shot:00873", "derived": "vlm + manual curation" }
}
```

## 9. Canonical roster ids (starter set)

| character_id | notes                                             |
|--------------|---------------------------------------------------|
| `nekron`     | gaunt sorcerer, white-reading hair, dark robe     |
| `larn`       | lead hero, blond, loincloth + arm bands + boots   |
| `teegra`     | lead heroine, pale two-piece                      |
| `darkwolf`   | rescuer, large warrior                            |
| `juliana`    | Nekron's mother, dark sorceress robes             |
| `king_jarol` | Fire Keep king                                    |
| `prince_taro`| Jarol's son                                       |
| `roliel`     | Frazetta-ref design (red hair, white robe)        |
| `otwa`       | Roliel's son                                      |
| `shaitan`    | Teegra's companion at Fire Keep                   |

Groups and creatures get the same treatment where they need a stable identity anchor;
propose ids as group slugs (`subhuman`, `dragonhawk_rider`) or creature slugs
(`dragonhawk`, `giant_octopus`, `swamp_lizard`). Only add a folder when there is a
canonical reference; a `draft` character with no `canonical_refs` is a placeholder, not
a record.

## 10. Conventions & invariants

- Every asset (character/garment/prop) has exactly one folder, one `manifest.yml`, and a
  `status` field. Every reference image has an angle name and, transitively, a status.
- VLM-reported colors outrank hand-typed names; correct silently in the manifest.
- ids are immutable and namespaced; a deprecated asset keeps its folder and files.
- Shot records reference ids only — never inline a garment's colors/materials (that info
  lives in the garment manifest, so it is versioned in one place).

## Migration note

Existing `refs/characters/<NAME>/traits.txt`, `refs/characters/<NAME>/vlm/*.json`, and
`library/char/sheet-runs/<NAME>_<seed>.json` (+ `seeds.tsv`) predate this schema and are
NOT retrofitted here. Adopting this schema means: promote `traits.txt` -> `manifest.yml`
per character, map sheet-run seeds -> garment/prop `version` lineage, and keep the old
files as history. Retrofit per-character as each lead's canonical refs are approved.