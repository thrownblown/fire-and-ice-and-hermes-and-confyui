# Sweeps → Shots v2 — Test Plan

*2026-10-26. Pipeline under test: the Krea2 character sweep (v2) feeding the
Qwen-Edit scene-setup path into H3 video. Follows the `T####` convention from
`docs/test-runs-plan.md` — one variable per test, one folder per run, Alex fills
the verdict after watching.*

## The pipeline (what "sweeps to shots" is)

```
Krea2 winner still ──▶ qwen_scene.py ──▶ scene still ──▶ review_scenes.py (32B)
   (character sheet)   (Qwen-Image-Edit      (character      GOOD/BAD
                        compose into scene)   placed in scene)
                                                        │ GOOD
                                                        ▼
                                          h3_scene.py (FL2VA I2V) ──▶ shot .mp4
```

v2 changed three things, each of which is now an untested assumption:

1. Sweep widened to **style × actor × base model × gens(4)** — 8 base models
   added, none of them verified for the technicolor register.
2. Scene stills are now **composed with Qwen-Edit** (`qwen_scene.py`, the
   `Qwen-Rapid-AIO-NSFW-v22` graph) instead of H3 painting the scene from text.
3. Scene stills are **VLM-reviewed** before H3 sees them.

What is already proven (do not re-test): the qwen_scene graph renders end-to-end
(darkwolf storm/megalith still, identity + gross anatomy clean), and the 32B
reviewer discriminates — it flagged fire-on-hands as BAD and passed the
hand-safe re-roll GOOD.

## Open questions → tests

Each test isolates ONE variable. Same seed / still / graph wherever a test
compares two things.

### T0020 — Sweep v2: base-model comparison
**Variable:** Krea2 base model (krea170277 / moody / kreamania / krast / +turbo
opt-in). **Held fixed:** char taro, style `30s+80s+rf` (the proven winner),
actor `person_11`, gens=4.
**Question:** which of the added bases are worth keeping for this register, vs
the old krea170277-only sweep?
**Run:**
```
.venv/Scripts/python.exe tools/subhuman_sweep.py --char taro --rig 4090 \
    --style 30s+80s+rf --actor person_11 --gens 4
.venv/Scripts/python.exe tools/review_sweep.py --char taro
```
**Artifacts:** 4 bases × 4 gens = 16 stills in `runs/subhuman-krea2/output/taro/`,
review in `taro_review.jsonl`, contact sheet.
**Optional repeat:** `--char nekron` (25/44 GOOD) — does a different base rescue
the weak non-humanoid anatomy, or is that a model ceiling?
**Verdict (Alex):** which bases survive / drop.

### T0021 — Qwen scene setup: identity hold across characters
**Variable:** the character being composed (does identity survive the edit?).
**Held fixed:** one shared scene prompt, one seed.
**Question:** does Qwen-Edit keep each character's face + costume when composing
into a scene, or does the base still's identity drift?
**Run:** `qwen_scene.py` per character, same prompt —
```
.venv/Scripts/python.exe tools/qwen_scene.py --base <winner still> \
    --prompt "place the character before a circle of standing stones at dusk, \
keep the face, hair and costume exactly as in the reference, full body, \
keep both hands clear" --char <c> --prefix t0021_<c> --seed 12345
```
Use winners for darkwolf, taro, teegra, juliana (male + female, both rig pools).
**Artifacts:** `scenes/stills/t0021_*.png` + a contact sheet pairing each winner
still next to its scene still.
**Verdict (Alex):** does identity hold across all four, or does it break on some?

### T0022 — Qwen ref slots: image1 vs +ref2 vs +ref3
**Variable:** which reference images feed the compose.
**Question:** does the source-film frame (`--ref3`) add pose/framing fidelity, or
does it drag the register back toward 1983 rotoscope (which we do NOT want)?
**Run (one char, e.g. darkwolf, same seed):**
```
(a) --base <winner>                                            # image1 only
(b) --base <winner> --ref3 <source film frame>                  # + source frame
(c) --base <winner> --ref2 <pose ref> --ref3 <source frame>     # all three
```
**Artifacts:** 3 scene stills side-by-side.
**Verdict (Alex):** which slot set to standardize on.

### T0023 — Qwen scene framing: 4:3 landscape vs portrait
**Variable:** scene output aspect (1280×960 vs 9:16 ~768×1368).
**Question:** the character stills are portrait; the qwen graph defaults to 4:3
landscape. Does the character get squished/stretched, and which framing suits
the film? (Also confirms the H3 FL2VA 0.4MP/32 portrait constraint downstream.)
**Run:** `qwen_scene.py` twice on one char, `--width 1280 --height 960` vs
`--width 768 --height 1368`.
**Artifacts:** 2 stills + a look at which one H3 accepts as `--still`.
**Verdict (Alex):** standardize 4:3 or portrait.

### T0024 — H3 I2V: text-scene (old) vs scene-still (new)
**Variable:** whether H3 gets a real scene still as first frame, or the bare
sheet + text scene.
**Question:** the whole point of v2 — does composing the scene still first hold
identity + motion better than H3 painting the scene from text?
**Run (same char, same H3 graph, same seed):**
```
# baseline already exists (old text path):
#   scenes/scene_darkwolf_darkwolf_30s+80s+rf_person_11_00002__00001_.mp4
# new: feed the approved scene still
.venv/Scripts/python.exe tools/h3_scene.py --still <approved scene still> \
    --char darkwolf --scene "<same scene text as baseline>"
```
**Artifacts:** 2 mp4s watched back-to-back.
**Verdict (Alex):** does the scene still beat the text path? (this decides
whether the Qwen step is worth it at all).

### T0025 — End-to-end pilot (darkwolf)
**Variable:** none — this is the integration check.
**Question:** is the full chain production-ready for the other 13 characters?
**Run:**
```
.venv/Scripts/python.exe tools/build_scenes.py --char darkwolf --review --render
```
**Artifacts:** winner → scene still → review verdict → shot mp4, one watchable
clip.
**Verdict (Alex):** green-light `build_scenes.py --all --render` or iterate.

## Order and dependencies

- T0021/T0022/T0023 (Qwen scene fidelity) can run **now** — they only need the
  existing winner stills, no long renders.
- T0024/T0025 depend on a scene still passing review, so run them after T0021.
- T0020 (base sweep) is the long-running, lowest-priority one — its verdict only
  decides which bases the *next* full sweep keeps, it does not block the scene
  path.
- Every verdict lands in `runs/INDEX.md` and an OptMem `--kind work` entry.
