# Direction: Fire & Ice remade as a TECHNICOLOR 80s sword-and-sandals EPIC

Set 2026-10-13. Alex's own words:

> "ok i think i have found my final direcrtion for this project. remake fire and ice as a
> **technicolor 80's sword and sandals movie**" — with the retro-fantasy LoRA linked
> (`civitai.com/models/2988830`)

> "i imagine like **halfway between ben hur and beastmaster with an unlimited effects budget**."

Source of the phrasing, and the fuller plan: Gemini share
`gemini.google.com/share/279c8e38f169` ("Remaking Fire and Ice in 80s Technicolor", 2026-10-13).

This supersedes the original reading of the project — that the output should look like the 1983
rotoscope **animation**. The content stays Bakshi/Frazetta; the **medium register changes** to the
live-action genre cinema of the era.

## What that means visually

Two poles, deliberately at once:
- **Ben-Hur (1959)** — the epic sword-and-sandals scale: enormous built sets, crowds, widescreen
  spectacle, saturated Technicolor, painted-backdrop depth. This is what "unlimited effects budget"
  buys: not a scrappy look, but the *big* look.
- **The Beastmaster (1982)** — the 80s barbarian-fantasy register: oiled muscle, leather and fur,
  high-contrast lighting, vivid colour, practical creature effects.

The shared visual language the prompts and plates must carry:
- **TECHNICOLOR** — vivid, hyper-saturated colour with deep blacks and high contrast. This is the
  single most important word in the brief, and it is the opposite of muted/brooding/faded.
  (An earlier draft of these strings said "slightly faded colour" — that was wrong and is fixed.)
- **epic practical scale** — built sets, crowds, matte-painted vistas, big staging
- **high-fantasy practical effects, executed on an unlimited budget** — practical in *aesthetic*,
  not in *limitation*: no visible-cheapness, no "rubber suit" reading
- **practical costumes and armour** — leather, brass, fur, hand-hammered metal
- **broad physical performance** with strong gesture; theatrical, not naturalistic
- **80s genre framing** — wide, confident, often heroic low angles

## Consequence 1 — the house style string changed (done)

The style line is centralised, so the direction applies at three sites. All three are updated:

| file | what it holds |
| --- | --- |
| `pipeline/fullrun.py` | `STYLE_BY_LOCATION` (4 location patterns) + `style_line()` default — the 3-field/FL2VA grammar |
| `pipeline/refrun.py` | the 6-field/REF2VA `summary` line |
| `pipeline/stage6_h3_prompts.py` | the `detailed_description` opener |

New shape, e.g. for interiors: *"an 80s sword-and-sandals fantasy film, shot on 35mm: torchlit
stone halls with heavy drapery and brass, theatrical painted sets, cold shafts of light through
high windows, soft analog photography and visible film grain"*.

The wording is a first draft — tune it freely. It is one table, so re-tuning is one edit plus a
prompt regeneration.

**Stale artefacts:** 494 files in `fullrun/prompts/` and 4 in `refrun/prompts/` still carry the old
"2D-animated rotoscope" line (plus 448 under `reports/` and 133 under `runs/`). They are generated
artefacts, not sources — regenerate, do not hand-edit.

## Consequence 2 — the reference stills now fight the style

Every reference still IS a frame of 1983 rotoscope animation. Feeding those to H3 asks it to
reproduce cel-animated ink figures while the prompt asks for 35mm live action. Two ways out, and
they are not exclusive:

- **(a) Style the start frames first.** The author of the retro-fantasy LoRA recommends exactly
  this — generate/prepare the frames in the target look, then animate them, and prefers a start
  frame over pure text-to-video. That makes our register **FL2VA / I2VA (Track B/C)** rather than
  REF2VA on raw animation stills.
- **(b) Keep the source stills for blocking only** and let the style LoRA plus the style string
  carry the look — REF2VA with the retention lines restricted to posture/timing/performance, not
  appearance.

This is the biggest open question the direction creates, and it is worth an A/B on one shot before
committing either way.

## Consequence 3 — the LoRA is the style vehicle

`MiniMax H3 — Forgotten World's "Retro Fantasy"` (docs/h3-loras.md) is authored for precisely this:
"the look and atmosphere of classic 1970s–1980s fantasy cinema… practical costumes, theatrical sets,
matte-painted environments… soft analog photography and that slightly imperfect cinematic texture
of old adventure films". UNET-only, rank 32, `LoraLoaderModelOnly`, optional trigger `retr0Fantasy`.
It is **not on the 5090** yet (only its step-3750 sibling is) — see docs/h3-loras.md for the fetch.

The author also notes the companion **Krea2 Forgotten World's LoRA** for establishing frames before
animating — relevant to Consequence 2(a), though that is a Krea2 LoRA on a different model.

## Consequence 4 — plates change character

The v3.1 plan called for "a generated Frazetta matte painting" per setup. Under this direction the
plate is **a matte-painted 80s film background**: photographic-ish, painterly where it must be,
with the era's colour and haze. `tools/plate_sketch.py` (Z-Image Turbo + Fun ControlNet, on the
4090) is the mechanism; the prompt changes, not the tool.

## What does NOT change
- Setups as the unit of work; plan by setup, never chronology.
- The two grammars and which model mode each pairs with.
- The ledger-driven motion rule (actions and camera moves come from `motion[]`/`shot_type[]`/`angle[]`).
- One camera move + one physical action per shot; camera vocabulary in natural English.
- Seed/length/step discipline from the community digest.

## The Gemini plan, checked against the repo

`gemini.google.com/share/279c8e38f169` lays out six phases. Most of it restates what the v3.1 plan
already locks, and the direction mapping is sound. Checked line by line, three things in it do not
match the repo as it stands:

| Plan says | Reality |
| --- | --- |
| "Run `stage7_assemble.py` … FFmpeg concatenation" | **`stage7_assemble.py` does not exist.** `pipeline/stage7_queue.py` is the queue. There is no assemble/stitch script in `pipeline/` at all — stitching currently lives in `runs/` drivers. |
| "output them to a human-readable markdown file (`sNN/1-shots.md`)" | **No `sNN/1-shots.md` files exist**, and there are no per-scene `sNN/` dirs. Shot inspection is the browser SPA (`browser/index.html`), which already shows start/mid/end stills per shot. |
| "swap out the dark fantasy Civitai LoRAs" | **We use no Civitai LoRAs at all** in the pipeline. The current stack is H3 turbo/ACC LoRAs. There is nothing to swap out; the retro-fantasy LoRA would be an *addition*. |
| "Manual Setup Clustering … group repeating camera angles into shared setups" | Already automated: `core/setups_v2.py` VLM-labels each shot and clusters them, written to `manifests/continuity_v2.jsonl` — including the S06-A and S06-E groupings the plan cites as examples. Manual review is still worth doing, but the file it wants already has this data. |

Also worth knowing: `sulphur_2_prompt_enhancer` is an LM Studio role, not a script — there is no
`prompt_enhancer` entry point in `core/` or `tools/`. The 4090 orchestrator step would need wiring.

Where the plan is right and worth following: everything about the ledger-driven motion rule, the
X4 no-concatenation rule, and the three tracks. And one genuinely useful prompt instruction — the
VLM is currently **omitting the style register** entirely, so if we keep a VLM in the loop its
labelling prompts should ask for technicolor-era descriptors ("vibrant technicolor", "cinematic
35mm", "high-fantasy practical effects") instead of its current default vocabulary.

## TEST 1 RESULT (2026-10-13) — the direction does NOT survive FL2VA on source stills

First real test: S05-c01 (Fire Keep study, 12.25 s, 294 frames, 20 steps), technicolor style string
+ `retro-fantasy-step00003750.safetensors` @ 0.8, same seed as the existing take. 322 s on the 5090.
Output: `renders/5090/video/S05-c01_technicolor_t01_00001_.mp4`.

**Verdict: the look did not change.** Sampled frames at 2 s and 9 s both still classify as 2D cel
animation, with muted/flat colour — not a live-action film frame.

**Mechanism, measured rather than argued.** The generated frame at t=0 differs from the source still
(`shot_00188_f00000.jpg`, the graph's `first_frame`) by a **mean absolute pixel difference of
5.6/255 = 2.2%**, and mean saturation only moves 0.613 → 0.650. The clip *starts as the exact 1983
animation frame* and never escapes it.

**Consequence:** FL2VA with source stills pinned as first/last frames is structurally incapable of
changing the medium register. A prompt and a style LoRA cannot override two pinned animation frames.
That kills the obvious approach — and the ones downstream of it, Track C (FFLF) and any Track B wired
to source stills — for **322 seconds of GPU time** instead of a day of character sheets.

This is Consequence 2 above, now confirmed by measurement: **the endpoints must be restyled first.**
The LoRA author's own advice points the same way (drive H3 from a prepared start frame).

### Next tests
1. **Restyle the endpoints** with Z-Image Turbo + the Fun ControlNet union, then FL2VA from the
   restyled first/last frames. Needs the **4090** (that is where the union controlnet and the
   plate tooling live). Blocked while LM Studio holds ~22 GB of 24.5 GB.
   Cannot run on the 5090: its `ModelPatchLoader` list is empty (no union controlnet) and it has no
   Qwen-Image-Edit base model.
2. **Control — DONE. The LoRA works, but it is not delivering the direction.**
   Same chunk, same seed, LoRA stripped (`--strip-lora`), 302 s. Frame-by-frame mean absolute pixel
   difference between the two takes:

   | t (s) | 0 | 2 | 4 | 6 | 8 | 9 | 11 |
   | --- | --- | --- | --- | --- | --- | --- | --- |
   | diff | **1.08 %** | 10.7 % | 14.7 % | 13.7 % | 13.9 % | 11.8 % | 9.5 % |

   So: **t=0 is identical in both takes** (1.08 % — the pinned source frame again), and the LoRA
   demonstrably changes the body of the clip by 10–15 %. It is wired correctly and it is doing real
   work. But mean saturation comes out *lower* with the LoRA (0.557) than without (0.598) — the
   opposite of technicolor. Conclusion: the LoRA is functional, the endpoints still dominate the
   register, and at 0.8 it is not producing the look on its own.
3. Only then: does a restyled endpoint + LoRA actually hold the look in motion.

## The question the plan ends on

It asks: rebuild the character sheets (Larn, Teegra, Darkwolf) first, or run a Track B probe on an
existing plate to see how the technicolor look handles the 1983 audio?

My read: **probe first.** The style string and the LoRA are the two new variables, and the whole
direction rests on whether they land on our actual source material. One Track B shot answers that
in a single render. Character sheets are ~a day of work each and would be redone if the look shifts.

## Open items
1. Tune the style wording — one table in `fullrun.py`, cheap to iterate.
2. Decide Consequence 2 — style-first frames vs source-stills-for-blocking. A/B on one shot.
3. Get the retro-fantasy LoRA onto the 5090 (fetch is in docs/h3-loras.md) and run the probe.
4. Re-examine the character descriptors in `fullrun.py`: `"SUBHUMAN": "a hunched fur-covered ape-like
   humanoid with primitive weapons"` is fine, but should now read as **practical creature makeup**
   on a big budget, and costume descriptions as period wardrobe rather than cel design.
5. Consider whether the VLM labelling prompts need the register vocabulary above.
