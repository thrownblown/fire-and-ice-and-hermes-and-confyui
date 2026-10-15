# Qwen Edit — Teegra upside-down bikini top (character sheet)

Source: Gemini thread share.gemini.google/XDe2Xf0OFJJK ("The Upside-Down Bikini Trend"),
Oct 14 2026. The bikini-top consistency problem: Krea 2 drifts wardrobe detail even at
fixed seed+prompt+LoRA (same jada+retro-fantasy config gave a keyhole-cutout halter in one
run and the correct gathered-center-seam V-neck in another). This is the wardrobe/hair/
jewelry/accessory consistency gap that motivated the identity-edit LoRA research.

## The upside-down top geometry (the precise fix)

Lavender thin-cloth upside-down string bikini top. The gathered/ruched edges that normally
sit flat under the bust are turned completely INWARD, running vertically facing each other
down the center of the chest. The thin strings from those center edges tie UP behind the neck.
The bottom points of the triangles point DOWNWARDS and OUTWARDS, wrapping under the bust and
tying around the back. High cleavage, deep V-neck halter illusion, revealing fantasy-barbarian
style. (Frazetta essentially predicted the 2020s upside-down-bikini trend in the early 80s.)

## Full character-sheet prompt (Qwen Edit / from-scratch generation)

A 1980s dark fantasy heroine in the style of Frank Frazetta and Ralph Bakshi animation. She
has long, flowing, jet-black hair parted down the middle, fair skin, and 1980s fantasy makeup
(winged eyeliner, muted red lips). She is wearing a lavender upside-down string bikini top.
The triangles are inverted: the gathered ruched edges run vertically facing each other down the
center of her chest, while the long bottom points of the triangles point downwards and wrap
around her back. The strings from the center of her chest tie behind her neck, creating a deep
V-neck halter illusion. She wears a thin black cord choker with a small gold diamond pendant,
and gold hoop earrings with dangling gold cones. Jungle or swamp background, cel-shaded
lighting, flat yet rich vintage animation colors.

## Clothing-edit-only prompt (mask/inpaint just the chest area)

A lavender upside-down string bikini top. The triangles are inverted: the straight ruched
edges face inward running vertically down the center of the chest. The strings from the vertical
center edges tie up behind the neck. The bottom points of the triangles aim downwards and wrap
under the bust to tie around the back. Halter-neck illusion, thin cloth, 1980s fantasy
barbarian style.

## Negative prompt (crucial for forcing the structural change)

standard bikini, horizontal underwire, normal swimwear, traditional triangle top, thick straps,
modern bikini, bandeau, one-piece, modern clothing, photorealistic, 3D render

## Qwen Edit tips

- If Qwen keeps "fixing" the top back to normal, use the negatives above and emphasize
  "inverted triangle top" / "criss-cross halter illusion."
- Qwen-Edit sees each input image at ~384x384 for meaning (plus ~1MP for appearance), so a
  small top detail can be invisible to the semantic encoder -> crop tight on the chest, not just
  prompt.
- Qwen-Edit re-synthesizes the whole frame (unedited regions drift; faces can change identity
  across a chain of edits) -> 2026 practice: Qwen-edit with a consistency LoRA, then inpaint the
  face back if it wanders. For a one-off top edit on a good face, a masked chest edit is the
  cleanest.
- Qwen-Edit and Krea 2 share the same VAE, so latents can be handed between them.

## 5090 Qwen-Edit readiness (checked)

Qwen-Image-Edit-2509 model files present on 5090:
  qwen/misc/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors
  qwen/misc/Qwen-Image-Edit-2509-Lightning-8steps-V1.0-fp32.safetensors
(plus Qwen2.5-VL-7B text encoder and Qwen Image VAE needed by the node.)

Teegra reference images available on the 4090:
  E:/FNI/refs/characters/TEEGRA/  (23 stills - real film stills; best source for the
  correct upside-down top). Pick one with a clear, upright chest view.

Note: the 4090 ComfyUI (127.0.0.1:8188) is the machine already running Qwen-Edit attempts;
the 5090 carries the Qwen-Edit model files. Confirm which box has the ComfyUI Qwen-Edit node
before testing - see qwen_edit_nodes_check.
