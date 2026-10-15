# Character-sheet comparison — Krea 2 vs Qwen Image 2.1 vs MiniMax H3 (video)

Source: https://www.youtube.com/watch?v=App5Rhnn-K0 — "Character Sheet Comparison &
Choosing Reference Images". Transcript pasted by Alex 2026-10-15.

A hands-on three-way test of one woman + one man + one cartoon character (an "angry
French fry") through the same character-sheet job on all three engines. This is the
exact FNI identity-sheet problem, so the verdicts map directly onto our pipeline.

## The three setups (all three are reference-conditioned, not pure T2I)

- **Krea 2** — set up to do a close-up then slowly turn the body across the sheet
  (a "turnaround" layout). ~1 min/sheet.
- **Qwen Image 2.1** — layout where NOT putting a separate head panel makes it focus
  on the larger full-body panel. ~1 min (but see the stall trap below). Holds the face
  closest to the reference.
- **MiniMax H3** — via **Sato Dive's** character-sheet workflow, with selectable style
  presets: `realistic`, `anime`, `3D like Pixar`, and a `preserve style` preset that
  copies the reference's style. ~2 min/sheet. The layout/setup is the best of the three,
  but the **face changes** vs the reference.

## Verdicts

| test | Krea 2 | Qwen 2.1 | MiniMax H3 |
|---|---|---|---|
| Woman #1 | face drifts slightly, hair held | **winner** — face closest to ref | face is different (identity drift) |
| Woman #2 | face changed a little, hair held | good | **winner** — "looks amazing" |
| Cartoon | **failed** — grabbed the sweater off the table (prompt problem) | **winner** — kept the style, 4/5 panels usable | changed style to 3D-realistic despite the preserve-style preset |

The cartoon test exposed that all three are **prompt-limited on non-human subjects** —
the Krea result ("disturbing") was a prompt, not a model, failure, and MiniMax's
preserve-style preset worked on SpongeBob in a prior test but not this one.

## Traps + fixes that matter for FNI

1. **Head-shot → swimsuit drift.** "If you just do a head shot, a lot of times with
   women you'll end up with them in a swimsuit or scantily clad. Use a full-body shot."
   → This is the SAME wardrobe-drift failure FNI hit on Teegra. At the sheet stage the
   cheap fix is: full-body reference, not head-shot. (The edit-model pass still covers
   residual drift.)
2. **Qwen stall at 8 min = image size / megapixels too high on a 16 GB card.** The fix
   was lowering the resolution; the corrected run took 30 s. → Before debugging a slow
   Qwen job, check the megapixel/resolution setting, not the model.
3. **MiniMax H3 identity drift is the recurring cost** of its otherwise-best sheet
   layout — face changes every time. → This is the core reason FNI's edit-model
   (Qwen-Edit) pass exists; the sheet layout is great but identity must be re-locked
   after.
4. **MiniMax style presets** (realistic / anime / 3D-Pixar / preserve-style) are the
   lever for the sheet's medium — worth pulling from Sato Dive's workflow instead of
   hand-rolling.

## FNI takeaway

- Qwen 2.1 is the **identity-holding** sheet engine (face closest to ref) — consistent
  with the reddit thread's 44/44 identity-coherence result. MiniMax H3 is the best
  *layout* but worst identity; Krea 2 is mid on both and the turnaround layout is its
  own thing.
- The "full-body not head-shot" rule is a one-line fix worth baking into the character-
  sheet tasks and the prompt-crafter contract (head shots invite swimsuit drift).
- Links the author promised (Sato Dive channel + workflow, Pixarroma LoRA, the free
  workflow) are in the video description — not captured here; pull if we adopt any.
