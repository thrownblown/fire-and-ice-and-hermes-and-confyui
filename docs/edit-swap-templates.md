# Edit-Swap Prompt & Parameter Templates (Qwen Edit / Klein Edit)

Reusable copy-paste templates for Stage 3 of the Krea→edit pipeline
(`docs/plans/2026-10-15-krea-to-edit-shot-pipeline.md`). These drive Qwen-Image-Edit
(primary) and Klein Edit (surface-only fast-path, gated on install confirmation) when
swapping not-quite-right wardrobe and props for the canonical asset-library versions.

Source of truth for every `{VARIABLE}` value: the asset manifest
(`docs/asset-schema.md`). Never type a color/material from memory — read it from the
garment/prop `manifest.yml`. VLM-reported color outranks hand-typed names.

---

## 0. Placeholder legend

| Placeholder | Where it comes from |
|---|---|
| `{TARGET_REGION}` | the named edit region, e.g. `garment:top`, `prop:<prop_id>` |
| `{GARMENT_ID}` / `{GARMENT_NAME}` | garment `manifest.yml` — `garment_id` / `name` |
| `{PROP_ID}` / `{PROP_NAME}` | prop `manifest.yml` — `prop_id` / `name` |
| `{COLOR_NAME}` | manifest `materials.color.primary_name` |
| `{RGB}` | manifest `materials.color.primary` (sampled triple) |
| `{MATERIAL}` | manifest `materials.material` (e.g. `woven cloth, matte`) |
| `{GEOMETRY_NOTES}` | manifest `notes` — the defining silhouette/fit detail |
| `{SLOT}` | one of `top / bottom / outerwear / shoes / accessory` |
| `{ACTION}` | `add` / `replace` / `remove` (props) |
| `{MASK_REGION}` | plain-English mask scope (torso, hand, whole-frame) |
| `{REF_PATH}` | repo-relative path to the approved reference image |

`{NEGATIVE_PROMPT}` and `{PRESERVATION_CLAUSE}` resolve to the fixed blocks in
sections 3 and 4 below.

---

## 1. Preservation clause (append verbatim to every template)

```
Preserve exactly: the character's face, facial features, hair, hairstyle, skin tone,
eye color, body proportions, pose, hands, camera angle, framing, background, and
lighting. Do not change, re-render, or alter any of these. Modify only the region
specified by {MASK_REGION}; every pixel outside that region must remain identical
to the input image.
```

This clause is mandatory in all four templates in sections 5–6. The acceptance
criteria for a Stage-4 review *fail* without it.

---

## 2. Swap-garment template

Single garment slot per pass. One pass = one `{SLOT}`.

```
Replace the garment in {TARGET_REGION} with the canonical reference garment.

Reference garment: {GARMENT_ID} — {GARMENT_NAME}.
Material and color (from the asset manifest — do not alter): {COLOR_NAME}, RGB {RGB},
{MATERIAL}.
Fit the reference garment to the figure exactly as worn in the approved reference,
including its defining geometry: {GEOMETRY_NOTES}.

Keep the pose, framing, camera, background, and lighting exactly as they are.
Replace ONLY the garment within {MASK_REGION}; leave the face, hair, skin, hands,
and body proportions identical to the base image.

{PRESERVATION_CLAUSE}

{NEGATIVE_PROMPT: garment}
```

---

## 3. Swap-prop template (with add / replace / remove)

Props route on `{ACTION}` to three sub-forms.

### 3a. Replace (the common case)

```
Replace the prop in {TARGET_REGION} with the canonical reference prop.

Reference prop: {PROP_ID} — {PROP_NAME}.
Material and color (from the asset manifest — do not alter): {COLOR_NAME}, RGB {RGB},
{MATERIAL}.
Scale and placement (from the prop manifest): {SCALE_NOTE}, {PLACEMENT_NOTE}.
Match the reference prop's shape and geometry exactly: {GEOMETRY_NOTES}.

Keep the pose, framing, camera, background, lighting, and the character's hands,
grip, and body proportions exactly as they are. Replace ONLY the prop within
{MASK_REGION}.

{PRESERVATION_CLAUSE}

{NEGATIVE_PROMPT: prop}
```

### 3b. Add

```
Add the canonical reference prop to the scene.

Reference prop: {PROP_ID} — {PROP_NAME}.
Material, color, scale, and geometry (from the prop manifest): {COLOR_NAME}, RGB {RGB},
{MATERIAL}; {SCALE_NOTE}; {GEOMETRY_NOTES}.
Place it: {PLACEMENT_NOTE}.

Do not alter the character, the existing wardrobe, or anything outside
{MASK_REGION}.

{PRESERVATION_CLAUSE}

{NEGATIVE_PROMPT: prop}
```

### 3c. Remove

```
Remove the prop from {TARGET_REGION}, leaving the natural background and the
character's hands/pose exactly as they were without the prop. Fill the vacated area
so it reads as the clean, original background/lighting.

Do not alter the character, the other props, or anything outside {MASK_REGION}.

{PRESERVATION_CLAUSE}

{NEGATIVE_PROMPT: prop}
```

---

## 4. Negative / guardrail phrasing

Resolve `{NEGATIVE_PROMPT: garment|prop}` by concatenating the **default block** plus
the matching **failure-mode blocks** (§4b) that apply to the pass. Blocks are plain
comma-separated negative strings — append them after the positive instruction.

### 4a. Default block (always include)

```
low quality, blurry, out of focus, jpeg artifacts, oversaturated, photo,
photorealistic, 3D render, text, watermark, cartoon
```

(Tailor `cartoon`/`photo` to the target medium; for the Technicolor 80s look keep
`photorealistic, 3D render` and drop `cartoon` if the house style leans painted.)

### 4b. Failure-mode blocks (add the ones that matter for this pass)

| Failure mode | Negative string to append |
|---|---|
| identity drift | `different person, new face, altered facial features, changed hairstyle, different eye color, different skin tone` |
| garment bleeding into background | `color bleeding, garment pattern bleeding onto skin or background, fabric merging with backdrop, smeared edges` |
| texture mush | `melted fabric, smeared texture, over-smoothed, plastic skin, loss of weave detail, no fabric texture` |
| extra limbs / hand mush | `extra arms, extra hands, extra fingers, missing fingers, fused fingers, deformed hands, extra legs` |
| accidental wardrobe change (garment pass) | `different garment, changed costume, added layers, removed garment, modern clothing, undergarment change` |
| prop drift (prop pass) | `wrong object, changed prop shape, resized prop, duplicated prop, prop bleeding into hand, melted prop` |

### 4c. Structural-override negative (Qwen garment geometry that won't hold)

When a Qwen pass keeps "fixing" a non-standard garment back to a normal one (the
Teegra inverted-bikini case), add a targeted negative that names the *default* the
model wants to fall back to:

```
standard bikini, horizontal underwire, traditional triangle top, thick straps, bandeau
```

Generalize the pattern: name the mundane default the model keeps snapping to, and
re-emphasize the distinctive geometry word in the positive prompt (e.g. "inverted
triangle", "criss-cross halter illusion").

---

## 5. Parameter defaults (per model)

**Qwen-Image-Edit is the primary edit model.** Klein Edit is a surface-only fast-path
that is **gated on install confirmation**; until then route every pass to Qwen (see the
pipeline spec §7 routing rule). Klein values below are starting points, marked
provisional.

### Qwen-Image-Edit (primary) — 2509 Lightning 8-step / 2511

| Parameter | Default | Notes |
|---|---|---|
| denoise / strength | **0.75** | 0.7–0.85. Higher = more aggressive re-synth (needed for structural geometry); lower = tighter least-change swap. 0.9+ only for whole-frame re-synth of a visually-invisible detail. |
| steps | **8** (2509 Lightning) / **20** (2511 full) / **4** (2511 Lightning-4) | Match the checkpoint actually loaded. Do not invent steps for a checkpoint that does not have them. |
| guidance / CFG | **2.5** | 2.5–4.0. Raise toward 4.0 when the pass must force a structural change against drift. |
| seed | **fixed per pass-chain** | Pick one seed when the pass starts, hold it across re-rolls of the *same* region; the only thing that changes on a failed re-roll is the prompt/mask, not the seed. Record the seed in `shot_edits.jsonl` `params.seed`. |
| mask feather | **24 px** | 16–32 px on a tight region. Expand feather (or switch mask source, §5.2 of the spec) if the swap edge seams. |
| reference images | **1** (garment/prop canonical ref) | 2509: 1 ref image; 2511: up to 3. Hand the *reference*, not a free-text description, so color/material comes from the asset record. |
| crop caveat | tight crop on the region | Qwen's meaning encoder sees ~384×384; a small top/prop detail can be semantically invisible. Crop tight on `{MASK_REGION}` before a small-detail pass. |

### Klein Edit (surface-only fast-path — provisional, gated on install)

| Parameter | Default | Notes |
|---|---|---|
| denoise / strength | **0.55** | 0.45–0.65. Surface-only (color/trim/texture on an already-correct garment). Do NOT use Klein for geometry or identity-adjacent regions — route those to Qwen. |
| steps | depends on checkpoint | Confirm the Klein-Edit node/checkpoint identity before fixing any value (open item, spec §9). |
| guidance / CFG | **2.5** | provisional; tune once the checkpoint is identified. |
| seed | **fixed per pass-chain** | same rule as Qwen. |
| mask feather | **16 px** | lighter touch → smaller feather is usually enough. |

**Routing reminder (from spec §7):** any pass touching garment *geometry*, silhouette, or
an identity-adjacent area → Qwen. Klein only for a thin surface change on a
single isolated region.

---

## 6. Filled-in example — Teegra halter top + obsidian dagger

Real character `teegra`, garment `teegra.top.halter`, prop `melee.obsidian_dagger`.
Values pulled from `docs/asset-schema.md` (+ the Gemini thread notes for the halter
geometry). Fully copy-paste runnable once the reference images are approved.

### 6a. Garment swap — the inverted bikini-top correction

```
Replace the garment in garment:top with the canonical reference garment.

Reference garment: teegra.top.halter — Teegra's halter top.
Material and color (from the asset manifest — do not alter): pale purple,
RGB (166, 133, 196), woven cloth, matte.
Fit the reference garment to the figure exactly as worn in the approved reference,
including its defining geometry: sleeveless, ties at the neck; an inverted triangle
top — the gathered/ruched edges run vertically facing each other down the center of
the chest, the thin strings from those center edges tie up behind the neck, and the
bottom points of the triangles point down and wrap under the bust to tie around the
back.

Keep the pose, framing, camera, background, and lighting exactly as they are.
Replace ONLY the garment within the chest / torso; leave the face, hair, skin,
hands, and body proportions identical to the base image.

Preserve exactly: the character's face, facial features, hair, hairstyle, skin tone,
eye color, body proportions, pose, hands, camera angle, framing, background, and
lighting. Do not change, re-render, or alter any of these. Modify only the region
specified by the chest / torso; every pixel outside that region must remain
identical to the input image.

low quality, blurry, out of focus, jpeg artifacts, oversaturated, photorealistic,
3D render, text, watermark, different garment, changed costume, added layers, removed
garment, standard bikini, horizontal underwire, traditional triangle top, thick
straps, bandeau, color bleeding, garment pattern bleeding onto skin or background,
melted fabric, smeared texture, over-smoothed, extra arms, extra hands, extra fingers,
deformed hands, different person, new face, altered facial features, changed
hairstyle
```

Notes for this pass:
- Route to **Qwen** (structural geometry — the inverted silhouette is exactly what
  Krea 2 drifted on).
- denoise **0.8**, steps **8** (2509 Lightning), CFG **3.5**, seed fixed, mask feather
  **24 px** on the chest bbox.
- If it snaps back to a normal top, crop tighter on the chest and keep the
  `standard bikini, bandeau` negatives.

### 6b. Prop replace — obsidian dagger

```
Replace the prop in prop:melee.obsidian_dagger with the canonical reference prop.

Reference prop: melee.obsidian_dagger — Obsidian dagger.
Material and color (from the asset manifest — do not alter): black glass blade,
simple bone hilt.
Scale and placement: about 28 cm, relative to an adult male hand; carried at the
hip, edge forward.
Match the reference prop's shape and geometry exactly.

Keep the pose, framing, camera, background, lighting, and the character's hands,
grip, and body proportions exactly as they are. Replace ONLY the prop within the
hip / hand region.

Preserve exactly: the character's face, facial features, hair, hairstyle, skin tone,
eye color, body proportions, pose, hands, camera angle, framing, background, and
lighting. Do not change, re-render, or alter any of these. Modify only the region
specified by the hip / hand; every pixel outside that region must remain identical
to the input image.

low quality, blurry, out of focus, jpeg artifacts, oversaturated, photorealistic,
3D render, text, watermark, wrong object, changed prop shape, resized prop,
duplicated prop, prop bleeding into hand, melted prop, extra arms, extra hands,
extra fingers, deformed hands, different person, new face, altered facial features
```

Notes for this pass:
- Route to **Qwen** (prop geometry/addition). Only route to Klein if the dagger is
  already correctly shaped and the pass is a pure color/material tint.
- denoise **0.75**, steps **8** (2509 Lightning), CFG **2.5**, seed fixed, mask
  feather **20 px** around the hip bbox.

---

## 7. Stage-3 field mapping (what to write into `shot_edits.jsonl`)

| Template | `target_region` | `garment_id` / `prop_id` | `params` |
|---|---|---|---|
| swap-garment | `garment:top` | `teegra.top.halter` | `{denoise, steps, cfg, seed, feather}` |
| prop replace | `prop:melee.obsidian_dagger` | `melee.obsidian_dagger` | same shape |
| prop add | `prop:<prop_id>` | `<prop_id>` | same shape |
| prop remove | `prop:<prop_id>` | `<prop_id>` | same shape |

`ref_paths[]` = the approved reference image path(s) used as vision conditioning.
`model` = `qwen` or `klein`. `status` = `ok` on pass-gate, `final` on Stage-4 accept.