# Test Runs + Final Deliverable Plan

*2026-09-27. For Hermes (4090, can reach the 5090). GhstClwd can't reach the LAN from Discord, so Hermes executes.*

## Final product (redefined)
The deliverable is **not** finished video. It's a **chunk pack**: for every chunk, a full H3 prompt plus a prepared set of input refs, Frazetta-oil-styled and blocked to the shot. Generation is then done semi-manually per chunk.

## Naming convention
Everything keys off one ID: **`sNN-cMM`** (scene from the beat sheet, chunk within the scene, zero-padded, no gaps).

```
FNI/
  chunks/
    s03-c01/
      prompt.txt                  # final H3 prompt (ref2v)
      chunk.md                    # lines, speakers, source timecodes, prev/next, shot list
      src/  s03-c01_src_sh00064_mid.jpg ...        # original frames (read-only)
      refs/ s03-c01_ref_JULIANA_01.png             # prepared input refs
            s03-c01_ref_LOC_icepeak-throne.png
            s03-c01_ref_BLOCK_sh1.png              # blocked composition per shot
  library/                         # reusable across chunks
    char/   JULIANA_sheet_v01.png  NEKRON_sheet_v01.png
    loc/    LOC_icepeak-throne_v01.png
  runs/
    T0001_s03_ref2v-srcstills/     # one folder per test run
      manifest.md
      s03-c01_T0001_t01.mp4
      s03-c02_T0001_t01.mp4
      s03_T0001_stitched.mp4
```

**Rules**
- Test run ID: `T####`, sequential, never reused. Folder = `T####_<scope>_<method-slug>`.
- Render file: `<chunk>_<T####>_t<take>.mp4`. Sorting by name = story order, so the stitch is `ls | sort | concat`.
- Library assets are versioned `_v01`, `_v02`. A chunk's refs record which library version they came from in `chunk.md`.
- `manifest.md` per run: date, method, model/workflow, settings, chunk list, which refs, verdict (✅ / ❌ / notes). Alex fills in the verdict after watching.
- `runs/INDEX.md`: one row per T#### (id, scope, method, verdict). This is the scoreboard.

## Test matrix (S03 first, then one action scene)
| Test | Method | Question it answers |
|---|---|---|
| T0001 | ref2v, **original stills** as refs | Does v3 prompt structure fix plot/speakers? (baseline) |
| T0002 | ref2v, **Frazetta-styled character sheets** as refs | Does style transfer on refs carry into H3 motion? |
| T0003 | ref2v, **styled sheets + styled location plate + blocking frame** | Does blocking hold composition/staging? |
| T0004 | **V2V** low adherence from source clip + styled refs | Is V2V better for action-heavy chunks? |
| T0005 | best of above on an **action scene** (S14 camp raid) | Does it survive fights and motion? |

Same chunks, same seed where possible, one variable changed per test. Watch S03 stitched after each one.

## Ref prep: where the 222-chunk job gets automated
It isn't 222 × hand work. It's three layers:

1. **Character sheets (~10–15, manual, done once).** Edit model: source still → Frazetta oil style. Alex approves. Front/3-4/profile if possible. These go in `library/char/`.
2. **Location plates (~15, semi-manual, done once).** One per canonical location from the beat sheet (Ice Peak throne hall, Fire Keep hall, Roliel's hut, jungle, ...). Source background frame → Frazetta oil, no characters.
3. **Blocking frames (per shot, automated + human QA).** Edit model inputs: source mid-frame (for pose and composition) + character sheet(s) + location plate → Frazetta-styled frame matching the original staging. Batch it on the 5090 via ComfyUI and produce a contact sheet per scene. Alex rejects bad ones and only those re-run.

Layers 1–2 are the only real manual effort. Layer 3 is a queue plus a thumbs-up/down review.

**Automation candidates later:** auto-pick the best source mid-frame per shot (sharpness, fewest captions), auto-crop characters for sheets, a contact-sheet review where you tick rejects and it re-queues only those.

## Style note
Frazetta image gen was uncanny before because it was **text-only generation**. Style *transfer* from real frames (pose/composition locked) is a different, easier problem. T0002 tells us fast whether it works.

## Don't
- Batch-render all 222 before T0001–T0003 have verdicts
- Change more than one variable per test
- Overwrite a render or reuse a T#### number
