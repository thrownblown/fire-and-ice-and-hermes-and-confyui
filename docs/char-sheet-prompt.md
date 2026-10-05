# Character sheet prompt

One workflow: `graphs/H3CharSheet.json`. Per character, change three things: the style image, the identity image, and the name in the prompt. Nothing else.

## Locked from the Teegra tests (2026-09-28)

- Layout that worked: four full-body views, front, side, three-quarter back, back. Not three.
- Style comes from a real reference image, not from text. Text-only style drifts to flat cel.
- Winner: `ComfyUI_00017_.png`, seed `896723655157649`, input `teegracover.jpg`. Saved as `library/char/TEEGRA_sheet_v01.png`.
- Runner-up: `00018`, seed `818377003165923`. Its portrait reads most like Frazetta's Teegra.
- Flat cel outputs (00009, 00011, 00015) are parked. Wrong style, and 00009 gave her green eyes.

## Decisions still open

These changed between sheets. H3 copies the reference, so each needs one answer before the sheet is used as a video ref.

- Earrings: oil sheets gave silver hoops. The roster says gold. Pick one.
- Necklace: the pendant changed shape and color every sheet. Pick one.
- Skin tone: darker and bronzer than the film, which matches the Frazetta cover. Fine, but it must be the same in every chunk.
- Body: curvier than the film's petite Teegra. A deliberate Frazetta choice. Decide it on purpose, because it becomes her design for every scene.

## Graph wiring

- Node 25, `ref_image_0`: the style plate. For Teegra that was `teegracover.jpg`. For the rest of the cast, a Frazetta oil.
- Node 28, `ref_images.ref_image_1`: a clean film still of that character. This is the identity. The graph as saved has only `ref_image_0`. Add the second slot before running anyone but Teegra.
- Node 12, `noise_seed`: lock the winner's seed. Change one thing per run.
- Node 47 scales the reference to 1 megapixel. Leave it. That is what dodges the 2048 input cap.

## Prompt (node 28)

Replace `<NAME>` and keep every other word.

```
integrated_multimodal_description:

subject_definitions:
<NAME> character from <Picture 2>, painted in the art style of <Picture 1>:

summary:
[reference generation] static image of a character sheet. Keep the identity, face, hair, costume and proportions of <Picture 2>. Paint it in the oil style of <Picture 1>.

retention_analysis:
<NAME>: fully_preserved.

detailed_description:
The target video is a static image of a character sheet on a plain white background. Each element is separate and does not overlap.

[Shot 1] static image. Neutral expression on every view.

1. On the left, a portrait (head and chest) of <NAME>, close up, neutral expression, white background.
2. In the center, four full-body views of <NAME>, neutral stance, arms slightly away from the body: straight from the front, straight from the side, three-quarter back, straight from the back.
3. On the right, exactly 6 circles, 2 columns by 3 rows, nothing else:
   circle 1: a single eye.
   circle 2: the mouth.
   circle 3: one ear with its earring.
   circle 4: a hair color swatch.
   circle 5: a skin color swatch.
   circle 6: an outfit fabric swatch.

overall_soundscape: N/A

non_diegetic_music: N/A
```

## What changed from the posted prompt, and why

- `iintegrated` was a doubled i. Removed.
- `retention_analysis` said `<GIRL>` while the subject was `<CHARACTER>`. One tag now, and it is the character's name.
- "keep the exactly same art style of Picture 1" copies the reference's style, which is right for Teegra's cover and wrong for a film still. Style and identity are now two pictures.
- The circles were asked for as a list of zones, and came back as 6 to 9 with repeats. They are now numbered, one per slot.
- `neutral expression` is in the portrait line. Every test sheet gave her the same worried face.
- Four views, matching 00017 and 00018, not the three the old prompt asked for.
