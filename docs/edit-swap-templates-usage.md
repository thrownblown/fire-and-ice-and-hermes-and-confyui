# Edit-Swap Templates — Usage Note

Companion to `docs/edit-swap-templates.md` (this task's deliverable). Short orientation
for whoever runs Stage 3 passes.

## How to use these templates

1. **Resolve `{VARIABLES}` from the asset manifest, never from memory.** Color, material,
   and geometry come from the garment/prop `manifest.yml` (`docs/asset-schema.md` §4/§5).
   VLM-reported color outranks hand-typed names — if they conflict, use the VLM value.
2. **One pass = one `{SLOT}` or one prop.** Run serially, not batched, so a failed pass
   rolls back independently (pipeline spec §5.3).
3. **Append `{PRESERVATION_CLAUSE}` verbatim** to every prompt — it is the Stage-4
   "identity/background untouched" gate. Never edit it out.
4. **Append `{NEGATIVE_PROMPT}`** = default block (§4a) + the failure-mode blocks (§4b)
   relevant to this pass.
5. **Route first.** Geometry / silhouette / identity-adjacent → Qwen. Surface-only tint on
   an already-correct garment → Klein (only once install is confirmed). Qwen is the
   default either way.

## Parameter quick-start

- Qwen (primary): denoise **0.75**, steps **8** (2509 Lightning), CFG **2.5**, mask
  feather **24 px**, **1** canonical ref image, **fixed seed per pass-chain**.
- Klein (provisional): denoise **0.55**, feather **16 px**; steps/CFG unset until the
  checkpoint identity is confirmed (spec §9 open item).
- Crop tight on small details — Qwen's meaning encoder is ~384×384; a tiny top or prop
  detail can be semantically invisible otherwise.

## Recording a run

Write one `manifests/shot_edits.jsonl` row per pass:
`shot_id, pass_no, model(qwen|klein), target_region, mask_source, garment_id/prop_id,
ref_paths[], output_png, params{denoise,steps,seed,feather}, status(ok|fail)`
(see `docs/plans/2026-10-15-krea-to-edit-shot-pipeline.md` §8 for the full contract).

## Known open items that affect these templates

1. **Klein Edit checkpoint/node identity + install box** — unconfirmed; Klein params are
   placeholders until settled.
2. **Which box runs the Qwen-Edit node** — model files on the 5090, current attempts on
   the 4090 (`docs/qwen_edit_teegra_prompts.md`); confirm before testing.
3. **Mask automation** — whether VLM bbox → mask is automated in-node or offline.