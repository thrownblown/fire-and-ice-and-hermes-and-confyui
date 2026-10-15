# Qwen Image 2.1 vs multi-stage turnaround — can one prompt replace the sheet pipeline?

Source: https://www.reddit.com/r/StableDiffusion/comments/1wmgbx9/can_qwen_image_21_replace_multistage_turnaround/
Author: HarnessLightnin (lab pipeline, "Blades '68" setting). Mined 2026-10-15.

## The question (maps 1:1 onto FNI's identity-sheet problem)

Their existing reference-sheet pipeline is H3 video turnaround → extract viewing
angles → stitch panels. They tested whether **Qwen Image 2.1 (7B DiT, bf16)** could
replace that with a **single T2I forward pass** producing a 4-panel composite sheet.

This is the same trade FNI faces: multi-stage H3 turnarounds vs a one-shot sheet.

## Test setup

- Model: `Comfy-Org/Qwen-Image-2.1` (7B DiT, bfloat16)
- Hardware: single RTX 3090 (24 GB), ~46.7 s/sheet, ~14 GiB peak VRAM
- 40 steps Euler/Simple, CFG 5.0, fixed seed
- 44 characters (humans + automatons)

Prompt: a fixed layout line + per-character wardrobe/chassis description + a fixed
style line. Layout held constant:

```
Character reference sheet, four panels arranged in a single composite image:
close-up portrait (top left), front view full body (top right),
rear view full body (bottom left), side profile full body (bottom right).
```

Style: "1968 photographic studio portraiture, crisp natural directional lighting,
fine fabric and material texture, sharp focus, neutral studio backdrop."

Key trick worth stealing: they **decoupled medium emulation** — pushed print/halftone
styling to deterministic downstream post-processing so diffusion capacity wasn't spent
on paper texture. (For FNI: the 80s retro-fantasy look would be a post-pass, not in the
sheet prompt.)

## What worked (44/44)

- **View compliance**: every sheet put the right view in the right quadrant. Zero swaps.
- **Identity & material coherence**: costume silhouette, palette, and surface material
  (chrome, etched brass) held across all four views *without reference-image conditioning*.

## What failed the human exit review (the blocker)

All three are framing/anatomy defects, NOT identity defects:

1. **Dwarfism** — some full-body figures compressed (oversized head, short limbs).
2. **Inter-panel camera distance drift** — the side profile framed closer than the
   front/rear; to fit, the model vertically compressed the anatomy.
3. **Edge/shin cropping** — front view head-to-toe, but rear cropped at shins and side
   at mid-thigh on the same sheet.

**Conclusion:** prompt-only Qwen 2.1 cannot *yet* replace the H3 turnaround. Prompt text
gives no lever to enforce camera distance or bounding boxes across panels. Next step they
flag: **lightweight structural conditioning** (fixed 4-panel pose skeletons or depth maps)
to lock camera distance without full video generation.

## Comments worth keeping

- **Vertical panels fix it** (listopalafoto, +4): "almost all open image models get
  shorter bodies or crop when the panel AR is horizontal or square. Vertical panels
  3:4 or 2:3 should improve results." → make each sheet panel portrait, not square.
- **Huge seed variation** (RiverSide71h): "tremendous seed variation with Qwen 2.1…
  if ever a model needed seed hunting." → seed hunting is mandatory, not optional.
- **LoRA from H3 outputs** (Responsible_Ad6964): "could prolly train qwen image 2.1
  lora from your h3 outputs." → a bridge from the H3 pipeline to a one-shot sheet model.
- **Hallucination across frames is subtle** (bstr3k): colors/patches mirror-image or
  drift; only visible on close look. → still needs a close review pass.

## FNI takeaway

- Qwen Image 2.1 is a real candidate to collapse FNI's per-character reference-sheet
  work (the kanban character-sheet tasks) into one T2I pass — but only if we accept the
  framing defects and fix them downstream, or add structural conditioning.
- The two cheap wins are directly applicable: (1) vertical 3:4/2:3 panels per quadrant,
  (2) seed-hunt rather than trust one roll.
- The "decouple medium emulation" rule reinforces the FNI split: Krea generates
  composition, the retro-fantasy LoRA/post-pass carries the look — don't ask the sheet
  prompt to do both.
- Identity coherence WITHOUT ref conditioning (44/44) is the headline — it means a
  single text description of Teegra could in principle hold across four views. But the
  framing failure is exactly the class of defect FNI's edit-model pass (Qwen-Edit) is
  already scoped to fix, so the two workstreams reinforce each other.
