# Character Appearance Consistency — the movie-like approach

Umbrella doc for the wardrobe/prop-consistency workstream. This is the entry point;
the five component pieces below are the authority for their slice.

## The idea in one paragraph

Krea 2 generates a shot, but its wardrobe and props **drift even at fixed seed + prompt +
LoRA** (the Teegra halter-top case: keyhole halter in one run, gathered-V seam in the next).
So we stop trying to prompt Krea into exact clothing. Instead we use a **two-hop** pipeline:

1. **Generate freely** with Krea 2 (rough wardrobe text only, composition/pose/lighting/likeness are what matter).
2. **Human approves** the still that gets composition + likeness right.
3. **Edit model swaps in** the canonical wardrobe and props, using approved reference
   stills from a versioned asset library.

The unit is the shot, but the pipeline is camera/chronology-agnostic — it runs per-shot
against the asset library, exactly like the existing setup-driven render pipeline.

## The five pieces

| Piece | File | What it is |
|---|---|---|
| Data model | `docs/asset-schema.md` | Namespaced ids for character/wardrobe/prop/shot; directory-per-asset + `manifest.yml`; five-slot garment taxonomy; `draft -> approved -> deprecated` lifecycle; the "approved reference" image rules. |
| Pipeline | `docs/plans/2026-10-15-krea-to-edit-shot-pipeline.md` | The 4-stage Generate -> Select -> Edit -> Review flow with inputs/outputs/pass-gates, the Qwen-vs-Klein routing rule, and the interface contract (`manifests/shot_approvals.jsonl`, `manifests/shot_edits.jsonl`, `renders/shots/<shot_id>/`). |
| Prompt templates | `docs/edit-swap-templates.md` (+ `-usage.md`) | Copy-paste Qwen/Klein prompts for garment swap and prop add/replace/remove, with a verbatim-preservation clause and negative/guardrail blocks for six failure modes. |
| Resolver | `tools/asset_library.py` + `tools/asset_lookup.py` | Turns a `shot_id` (or character+wardrobe+prop ids) into an ordered reference-image pack (`fni.asset/pack/v1` JSON). Fails loudly on missing/dangling assets. 9 pytest cases pass. |
| Pilot | `docs/pilot-report.md` | Teegra run 2026-10-15: Stage 1+2 succeed, Stage 3 blocked on one missing model file. |

## Asset identifiers (the spine of the system)

    character   = roster slug            e.g. teegra, darkwolf
    garment     = <character>.<slot>.<slug>   e.g. teegra.top.halter
    prop        = <category>.<slug>           e.g. melee.obsidian_dagger
    shot        = existing shot:NNNNN key     e.g. shot:00023

Slots: `top`, `bottom`, `outerwear`, `shoes`, `accessory`. A full-body garment is
`outerwear` with `covers: ["full"]`. Only `approved` assets may feed a generation or edit
prompt; `deprecated` ids are never reused.

## Routing rule (edit stage)

- **Qwen-Image-Edit-2509 = primary.** Structural/geometry/fidelity edits; shares Krea 2's
  VAE so latents can be handed between the two models. Re-synthesizes the whole frame, so
  watch for face/comp drift across an edit chain.
- **Klein (Flux2Klein) = surface-only fast-path**, gated on install confirmation. Not yet
  confirmed present on either box — keep provisional.

## Where it stands today (pilot verdict: CONDITIONAL GO)

Generate -> Select -> Asset-pack are **proven** end-to-end on the 5090 (clean 1980s-fantasy
base still + a valid pack JSON). The edit half is **~90% infra-ready**: edit nodes +
fp8 checkpoint + VAE are all live; **one model file is missing**.

Three things blocked the pilot's Stage 3, in priority order:

1. **Qwen-Image-Edit-2509 text encoder missing.** The fp8 checkpoint is diffusion-only and
   returns a null CLIP, and Qwen2.5-VL-7B is not in the clip directory. Fix: download
   Qwen2.5-VL-7B-Instruct in ComfyUI `qwen_image` format to the 5090, wire it via
   `CLIPLoader(type=qwen_image)` instead of taking CLIP from `CheckpointLoaderSimple`.
   One ~15 GB file unblocks the whole edit path.
2. **The saved Krea2 workflow is not production-clean** — it ships an explicit adult prompt
   and two live celebrity-likeness LoRAs (@ 0.7 each, names withheld in this repo). Publish a scrubbed
   "house" template with those defaulted OFF and only the retro-fantasy house LoRA live.
3. **Asset refs are placeholders, not garments.** The library's only character (aria) points
   at 32x32 colour swatches; the real Teegra stills live un-ingested at `refs/characters/TEEGRA/`.
   Ingest them (`face.front`/`body.front`/`top.halter`/`dagger` → `assets/characters/teegra/…`,
   `status=approved`) before any real edit — a 32x32 block cannot drive a garment swap.

## Next step (explicit, do not fan out before it)

Install Qwen2.5-VL-7B + ingest the real Teegra stills, then complete **one** end-to-end
garment swap (Teegra halter) and use that single shot to validate identity-preservation and
re-synthesis drift before scaling the edit pass to the full cast.