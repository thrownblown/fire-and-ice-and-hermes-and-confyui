# Audio / Voice Plan

*2026-09-27. Decide by testing, not by arguing. Both paths are cheap because the SRT gives exact timecodes for every line.*

## Options
| | Approach | Pros | Cons |
|---|---|---|---|
| **A** | **Original audio laid over the generated video.** Mute H3 audio; use the film's audio for the chunk's source timecode. | Real performances and real score, zero voice work, and timing already matches since chunks are cut to source timecodes | Lip sync won't match the new animation (rotoscope style is forgiving); can't do new lines (cut Darkwolf ending, alt Larn) |
| **B** | **H3 audio reference.** Feed per-character voice samples (from the film) as audio refs; H3 generates the dialogue. | Lip sync matches; works for new/cut lines; consistent per character | Voices drift; delivery is weaker than the actors; music has to be handled separately |
| **C** | **Hybrid.** H3 generates with voice refs for lip sync, then the final mix swaps in the **original dialogue stem** where it exists, and keeps H3 voice only for new lines. | Best of both | Two passes, more mixing |

**Likely winner:** C, falling back to A for dialogue-heavy scenes if H3 lip sync is weak. B only for lines that don't exist in the film.

## Step 1: Stem separation (once, whole film)
Run Demucs or UVR (MDX/Kim vocal model) on the full audio track on the 5090:
- `audio/stems/dialogue.wav`: voices
- `audio/stems/music_sfx.wav`: score + effects

This makes A and C clean. The score becomes its own layer (non_diegetic_music becomes real, not described).

## Step 2: Voice sample library (from the SRT, automated)
For each character, auto-cut every HIGH-confidence line from `dialogue.wav` using the timeline timecodes (±0.15s padding):
```
audio/lines/L024_JULIANA.wav
audio/lines/L025_NEKRON.wav
...
```
Then Alex picks the **3–5 cleanest per character** (no music bleed, no overlap, emotional range) and puts them in:
```
library/voice/JULIANA_ref_01.wav ... (10–30s total per character)
```
Contact sheet: `audio/voice-review.md` lists each character's candidate clips with line text and duration, so Alex listens and ticks the ones to keep.

Characters with enough lines for a solid sample: Larn, Teegra, Nekron, Juliana, Darkwolf, Jarol, Taro, Roliel, Spirit. Minor ones (Tutor, Envoy) can use whatever exists.

## Step 3: Per-chunk audio assets
Every chunk folder gets:
```
chunks/s03-c01/audio/
  s03-c01_orig_full.wav        # original mix for the chunk's source window
  s03-c01_orig_dialogue.wav    # dialogue stem, same window
  s03-c01_orig_music.wav       # music/sfx stem, same window
```
The prompt's voice refs point to `library/voice/<CHAR>_ref_*.wav` for the speakers in that chunk.

## Tests (add to the test-runs matrix)
| Test | Method |
|---|---|
| T0006 | S03, H3 with **voice refs** (B). Is lip sync and voice identity good enough? |
| T0007 | S03, same video as T0006, **original dialogue + music stems** overlaid (C). Compare side by side. |
| T0008 | S03, **original full mix** over T0001 video (A). Baseline. |

Alex watches all three stitched. Verdict decides the default per scene type (dialogue vs action).

## New lines (no source audio)
- **Cut Darkwolf ending** (Juliana: "You came back." / "What have we done to our children?", Darkwolf, Nekron's death scream): H3 voice refs from the samples, or a voice-cloning TTS trained on the same samples. Mix under the original score style.
- **Alt fem Larn:** no source voice. Pick or design a voice (low, husky, calm), make 3–5 reference clips with TTS/voice design, and store them as `library/voice/LARN_F_ref_*.wav`.

## Note
Cloned voices of the original actors are fine for a personal project. Think twice before publishing anything that puts new words in real actors' voices.
