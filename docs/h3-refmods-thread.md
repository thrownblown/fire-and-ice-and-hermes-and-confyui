# r/StableDiffusion — "H3 RefMods are great I highly advice trying it out" (1wclxbj)

Source: https://www.reddit.com/r/StableDiffusion/comments/1wclxbj/h3_refmods_are_great_i_highly_advice_trying_it/
Choowkee, 2026-09-10, 153 up, 89 comments. Pulled 2026-10-12.
Third RefMod thread; the other two are 1x4auud (Dainamo's workflow) and 1w8ik7a (malcolmrey's models).

## The claims, with the counter-claims
- Works as a "light LoRA" for H3 ref models, and with FL2VA too (Choowkee). 8 images → refmod in
  "a couple of minutes".
- **Speed is the main win**: refs baked to latents once, not re-encoded every run. Measured
  reports are modest — not_food: **~7% faster** than image refs, same seed gives the same result;
  crinklypaper: **10–20 s** difference on a 9-image workflow. The bigger win is not having to drag
  images onto a fresh cloud instance (Choowkee).
- Capacity: the normal flow caps at ~8–9 images; a refmod packs more (malcolmrey goes with Luisa's
  higher figure). OOM avoidance when referencing many objects.
- Identity: several users report better likeness from a refmod of 6+ images than from character
  sheets or a handful of refs, "less plastic skin, face more coherent when distant"
  (EvidenceMinute4913, Party_Mode_2690). Others report **character bleed** once two refmods are in
  the same shot (ILikeStealnStuff, Nguyenkain, SiliconPyro — "half the time I get one of them
  twice, usually the second one selected in the loader").
- **Size matters:** oversized refmods slow generation (Iamcubsman: 5–8 MB refmods vs malcolmrey's
  ~1 MB). oppai: fewer tokens = faster.
- Refmods do NOT respect `extra_model_paths.yaml` (not_food).

## Corrections to our own notes
1. **Voice in refmods is NOT settled.** kami77: "the audio implementation for voice timbre matching
   doesn't seem to be quite there yet", and visual+audio refmods can't be tagged directly (the
   experimental node doubled generation time). This is in tension with the second-hand claim in our
   skill that a long voice sample clones ~1:1 — treat that as unverified.
2. **Background bleed is the failure mode that matters to us.** InariKirin: the refmod's own
   background leaks into the output and the prompt can't override it. The fix that worked for them:
   strength AND retention both = 1, and supply the environment as **First Image** with a
   `<Picture 1>` line in the prompt. Extra step (generate the background separately) but stable
   results. DIRECTLY relevant: FNI's master plates are generated separately by design, so the
   refmod must not import the source background. Our recipe already sets `background_retention=0`;
   this thread says that alone may not be enough.
3. A character refmod frees the `<Picture>` slots for body/clothing/other subjects — you can mix a
   refmod (identity) with plain reference pictures (body, costume).

## Prompting refmods (the recurring confusion, resolved)
- Always `<Subject N>` — never `<Picture N>`/`<Background N>`/`<Pose N>`. "Just like with regular
  H3, you always use Subject as the anchor regardless of concept" (Choowkee). A location refmod is
  `<Subject 2> is the modern city with tall skyscrapers`.
- Multi-refmod no-bleed recipe (EvidenceMinute4913): define `<Subject 1>`/`<Subject 2>` **in the
  order the refmods are loaded in the loader**, describe each one's physical attributes, repeat
  those attributes in `retention_analysis`, then tag them normally in `summary` and
  `detailed_description` — including a parenthetical attribute reminder at each use
  ("a man wearing plate armor and red cape (<Subject 1>) ...").
- Static shots: put "A medium static shot" in `summary` AND "Static shot" in
  `detailed_description` (Choowkee). Others find "cinematic static shot" stops working with
  refmods and the shot changes randomly.
- The model matches against the refmod's encoded latents; if your prompt names nothing that's in
  them, it falls back to the DiT's own prior (mimeniia). So remember the composition of the images
  you baked.

## Tooling
- Base pack: `Luisacaotica/ComfyUI-MiniMaxH3Mod` (`H3RefModCreateFromFolder`).
- Fork with audio + video refmods and a **visual refmod picker**:
  `github.com/FranckyB/ComfyUI-H3RefMods` (Niko3dx built ~200 character refmods with it; the picker
  loads likeness+audio in one click). Guide: malcolmrey's
  `MINIMAX_H3_REFMOD_CREATION_GUIDE.md` / `..._INSTALLATION_AND_USAGE_GUIDE.md` on the HF datasets
  repo.
- Minimum viable create graph: `Load image → Create H3 RefMod → Save H3 RefMods` (Choowkee).
- malcolmrey's own workflow: "make me refmod from this folder" — fully agentic.
