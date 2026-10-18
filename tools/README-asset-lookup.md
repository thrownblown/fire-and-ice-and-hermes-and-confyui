# Asset lookup — reference-image packing for the edit stage

Resolves a shot, or a character plus wardrobe/prop ids, into the exact reference
images and metadata the Krea -> Qwen/Klein edit stage needs, as a single JSON payload.

Schema: `docs/asset-schema.md`. Directory-per-asset + one `manifest.yml` per folder,
no database. Only `approved` assets with `approved` references may be packed.

## Files

- `tools/asset_library.py` — importable resolver (`build_pack`); no CLI, no paths baked in.
- `tools/asset_lookup.py`   — the CLI wrapper.
- `assets/`                 — sample library (character `aria`, garments, a prop, a shot).
  The PNGs are coloured 32x32 placeholders, not approved reference photography.
- `tests/test_asset_lookup.py` — pytest coverage of the acceptance criteria.

## Run the example

From the repo root:

```
python tools/asset_lookup.py --root assets --character aria --wardrobe coat_02 --prop lantern_01
```

This resolves the bare slugs `coat_02` -> `aria.outerwear.coat_02` and `lantern_01` ->
`set-dressing.lantern_01`, validates every manifest + every reference file exists and is
`approved`, and prints one JSON object (schema `fni.asset/pack/v1`):

```
{
  "schema": "fni.asset/pack/v1",
  "request": { "character_ids": ["aria"], "wardrobe": ["coat_02"],
               "props": ["lantern_01"], "shot_id": null },
  "reference_images": [
    { "role": "character", "asset_id": "aria", "angle": "face.front",
      "rel": "characters/aria/refs/face.front.png", "path": ".../face.front.png",
      "status": "approved" },
    ... 11 entries total, in a fixed order ...
  ],
  "description_block": "Character: Aria (aria)\n  ...\nWardrobe: ...\nProp: ...\n",
  "validation": { "ok": true, "errors": [] }
}
```

Ordering is deterministic: character identity refs first (`face.front`, `face.profile`,
`body.front`, `body.back`), then each requested garment (`front`, `back`, `side`, then any
`detail.*`), then each requested prop (same angle order).

`description_block` is the prose block that can be dropped straight into the edit prompt
template — it carries the distinguishing traits, curator notes, colour/material, and scale.

## Modes

- By id: `--character <id>` (repeatable), `--wardrobe <id|slug>` (repeatable), `--prop
  <id|slug>` (repeatable).
- By shot: `--shot shot:00023` reads `assets/shots/shot-00023.yml` and resolves every
  character/wardrobe/prop listed in it.

Wardrobe and prop flags accept either a full namespaced id
(`aria.outerwear.coat_02`, `set-dressing.lantern_01`) or a bare slug (`coat_02`,
`lantern_01`). A wardrobe slug is resolved against the given `--character`; a prop slug is
resolved against the global `props/` directory and must be unambiguous.

## Failure behaviour

Any missing manifest, missing reference file, or non-`approved` asset makes the command
print a JSON error to **stderr** and exit `1`:

```
$ python tools/asset_lookup.py --root assets --character aria --wardrobe leggings
{ "schema": "fni.asset/pack/v1", "reference_images": [], "description_block": "",
  "validation": { "ok": false, "errors": [
    "wardrobe 'aria.bottom.leggings' is not approved (status='draft'); only approved assets may be referenced"
  ] } }   # exit code 1
```

All errors are collected and reported together.

## Paths

No absolute paths are hard-coded anywhere in the code. `--root` defaults to `./assets`
(relative to the current directory). Output image paths are emitted both as `rel`
(root-relative, portable) and `path` (absolute, computed at runtime for immediate loading).

## Windows note for shot records

The schema names shot files `<shot_id>.yml`, but Windows filenames cannot contain `:`, so
`shot:00023` is stored on disk as `shots/shot-00023.yml`. `--shot` performs the `:` -> `-`
mapping automatically.