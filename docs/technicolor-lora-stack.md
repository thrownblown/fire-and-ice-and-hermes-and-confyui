# Technicolor stack — LoRAs to download (2026-10-13)

Research intake for the pivot in `docs/plans/direction-80s-sword-and-sandals.md`: Fire & Ice
remade as a **Technicolor 80s sword-and-sandals epic** (Cleopatra / Ben-Hur × Conan / Beastmaster).

Toolchain the user named: **Krea 2** for stills (character LoRAs already exist), **Qwen-Image-Edit
2511** for restyling/edits, **MiniMax H3 or LTX-2.3** for video.

**Downloading from Civitai needs an API token from this box.** Plain `curl` gets either a 401
(no User-Agent) or, with `-A "Mozilla/5.0"`, an HTML **login page returned as HTTP 200** —
a ~9.8 KB `.safetensors` that fails to load. Grab the token from civitai.com → account →
API Keys, then:

```bash
TOKEN=xxxxxxxx
curl -4 -L -A "Mozilla/5.0" -H "Authorization: Bearer $TOKEN" -o out.safetensors "<url>"
```

Verified 2026-10-13. The URLs below are the correct `api/download` endpoints.

**Status after the first pass (same day):** #3 `80sFantasy_Krea2Raw_000004500.safetensors` and
#4 `30sTechnicolor_Krea2Raw.safetensors` **are on disk** (228.6 MB each, safetensors header parses,
513 tensors, `diffusion_model.blocks.*.lora_{A,B}`, `__metadata__.ss_base_model_version = krea2`).
#1 Technicolor Style and #2 Peplum are the two Civitai gates behind a login (9787-byte HTML page
returned with HTTP 200) — those two need the token; the ArsMachina pair does not.
Do not trust the byte count alone: a `.safetensors` under ~10 KB is the login page.

---

## A. 4090 (`E:\comfymodels\models\loras\krea\`) — Krea 2 still style layer

These stack ON TOP of the existing character LoRAs (`krea2_*_onetrainer.safetensors`) — style and
identity are separate axes on Krea 2. Load order: base → character LoRA → era/Technicolor LoRA.

| # | LoRA | Civitai | File / size | Trigger | Strength | URL |
|---|------|---------|-------------|---------|----------|-----|
| 1 | **Technicolor Style \| KREA 2 & ZIT** (patrik) | 2629410 v3124790 | `TechnicKrea2_c1-st3000.safetensors` 224 MB | none | 0.8–1.2 | https://civitai.com/api/download/models/3124790?fileId=3005262 |
| 2 | **Technicolor Peplum Vintage Style [KREA2]** (LolTurdFerguson) | 2803264 v3160456 | `technicolor_peplum.safetensors` 218 MB | `d@rk1980` | 1.0 | https://civitai.com/api/download/models/3160456?fileId=3040870 |
| 3 | **80s Fantasy Movie** (ArsMachina) | 789313 v3091396 | `80sFantasyKrea2Raw_000004500.safetensors` 223 MB | `ArsMovieStill, 80s Fantasy Movie Still` | 1.2 | https://civitai.com/api/download/models/3091396?fileId=2970876 |
| 4 | **30s Technicolor Movie** (ArsMachina) | 886686 v3134593 | `30sTechnocolorKrea2Raw.safetensors` 224 MB | `ArsMovieStill, movie still from a 1930s technicolor movie` | 1.2 | https://civitai.com/api/download/models/3134593?fileId=3015329 |
| 5 | Forgotten World's Retro Fantasy Krea2 (alt) | 2976904 v3374094 | 569 MB | none (optional trigger) | 1.0 | https://civitai.com/api/download/models/3374094 |
| 6 | Forgotten Cinema Technicolor Dreams (alt) | 2981349 v3379649 | — | none | 1.0 | https://civitai.com/api/download/models/3379649 |
| 7 | Technicolor by Fortnox (alt) | 2977069 v3374299 | — | `technicolor, dye-transfer process, deep rich reds` | 1.0 | https://civitai.com/api/download/models/3374299 |
| 8 | Technicolor Style — ZIT variant (only if Z-Image is used for plates) | 2629410 v2952186 | `Technicolor EP5.safetensors` 180 MB | `technic0lou_r` | 0.5–0.8 | https://civitai.com/api/download/models/2952186?fileId=2831492 |

**#1 and #2 are the two to actually try first.** #1 is the generic Golden-Age grade; #2 is the
sword-and-sandal/peplum one (the literal Ben-Hur register). #3 is the 80s-fantasy register with
matched H3 coverage (see section B) — it is the only style that exists for *both* stills and video
from the same author, which makes Krea-2-still → H3-video style continuity a one-variable story.

Notes from the model pages / comments:
- #1 at full strength pulls mid-century **wardrobe, hair and cars**; at ~0.6 it is grade-only and
  reads as 70s/80s. For FNI the ~0.6–0.8 band is the safe default, 1.0+ only when you want the
  period look to rewrite costume.
- Krea 2 alone is regarded as weak at "movie aesthetic"; these LoRAs exist precisely to fix that.
- All four are Krea-2-native (`LoraLoaderModelOnly` or `LoraLoader` on the MODEL chain). They are
  **not** interchangeable with the ZIT/Klein/Anima variants of the same model pages.

Local Krea 2 stack on the 4090: `Krea2_Turbo_convrot_int8mixed.safetensors` (base), `krea2` CLIP
type (`qwen3vl_4b` bf16 for the reference/vision path), `qwen_image_vae`. Also already present:
`krea2_identity_edit_v1_2`, `krea2_style_reference`, `krea2_reference_v1` companion node
(KonokoAz `ComfyUI-Krea2-Reference`) — that node does "character from Picture 1 in the exact style
of Picture 2" via native Qwen3-VL vision tokens, i.e. a second route to character+style fusion
that does not need a style LoRA at inference.

## B. 5090 (`~/comfyvenv/ComfyUI/models/loras/h3/`) — MiniMax H3 video style layer

| # | LoRA | Civitai | File / size | Trigger | Strength | URL |
|---|------|---------|-------------|---------|----------|-----|
| 1 | **30s Technicolor Movie** (ArsMachina) | 886686 v3339781 | `30sTechnicolorMovie_minimaxh3_3339408_epoch_10.safetensors` 296 MB | `ArsMovieStill, movie still from a 1930s technicolor movie` | 1.2 | https://civitai.com/api/download/models/3339781?fileId=3226392 |
| 2 | **80s Fantasy Movie** (ArsMachina) | 2946830 v3337011 | `80sFantasyMovie_minimaxh3_3333584_epoch_10.safetensors` 296 MB | `ArsMovieStill, 80s Fantasy Movie Still` | 1.2 | https://civitai.com/api/download/models/3337011?fileId=3223514 |
| 3 | **Forgotten World's Retro Fantasy** — the *missing* file of a version already half-on the box | 2988830 v3388934 | `retro-fantasy.safetensors` 569 MB | `retr0Fantasy` (optional) | 1.0 | https://civitai.com/api/download/models/3388934?fileId=3278075 |
| 4 | Cinematic Fantasy (alt) | 2957855 v3350636 | — | none | 1.0 | https://civitai.com/api/download/models/3350636 |
| 5 | CinemaGrade — MiniMax H3 Style LoRA (alt) | 2927223 v3312531 | — | `cinemagradestyle` | 1.0 | https://civitai.com/api/download/models/3312531 |

Run these on the box with `bash tools/download_5090_models.sh lora-technicolor` (added to that
script alongside `lora-retro-fantasy`).

**Author guidance that matters for our pipeline (ArsMachina, both H3 pages):**
- Style is images-only, so the video strength comes from locking *every frame* to the look, not
  from motion training. Best results on **FL2V or hybrid (T2I → I2V/FL2V)** — i.e. our Track B/C,
  not raw REF2VA on 1983 animation cells. The 80s Fantasy page explicitly recommends generating
  the first frame in **Krea 2** and applying the LoRA at REF2V.
- **Turbo LoRAs diminish the style**: when combining with a 4/8-step turbo, raise the style LoRA
  to **1.2–1.7** instead of the usual 1.0. This is the one stacking rule to respect.
- Neither H3 LoRA carries an fl2va/ref2va marker — plain DiT style LoRAs, `LoraLoaderModelOnly`.

Already on the 5090: `h3/retro-fantasy-step00003750.safetensors`, `h3/retro-80s.safetensors`
(a different, older retro LoRA) — both unjudged.

## C. Qwen-Image-Edit 2511 — the restyle bridge

Present: `qwen_image_edit_2511_fp8mixed.safetensors` (4090 `diffusion_models/qwen/`),
`qwen_image_edit_2509_fp8_e4m3fn_scaled.safetensors` + `qwen_image_vae` + `qwen_2.5_vl_7b_fp8_scaled`
text encoder; 5090 has 2509 + `Qwen-Image-Edit-2509-Lightning-8steps` LoRA.

- 2511 upgrade over 2509: better edit consistency (less drift), **up to 3 reference images**,
  multi-person fusion, and several community LoRAs folded into the base. Optional
  `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16` for 4-step speed.
- Role in this pivot: it is the **conversion pass**, not the generator — take a 1983 source still
  (or a Krea 2 still) and instruct the edit ("re-render as a 1950s Technicolor sword-and-sandal
  film still, practical costumes, painted matte backdrop"). Output becomes the H3 first frame.
- This is the concrete answer to "Consequence 2" in the direction doc: style the start frame first
  (Krea 2 or Qwen-Edit), then animate — instead of asking H3 to restyle rotoscope cells while
  REF2VA holds them.

## D. Video model choice: H3 vs LTX-2.3

| | MiniMax H3 | LTX-2.3 (22B) |
|---|---|---|
| On the 5090 | official fl2va/ref2va int8, Singularity, Ref-Delta-Fused, w4a8 | `ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled` + LTX23 VAEs + text projection |
| Style LoRAs for *this* look | **yes** — the two above | **no** equivalent Technicolor/era LoRA exists |
| What LTX has | — | IC-LoRAs (union/canny-depth-pose control, water sim, detailer), camera LoRAs, ID-LoRA, distilled speed LoRA |
| Audio | native audio VAE + our whole audio pipeline | native synced audio, but no FNI audio stems work yet |

**Read: H3 stays the video model for the style**; LTX-2.3 is the fallback for length/speed or for
structure transfers (IC-LoRA can carry camera/motion from a reference clip). LTX LoRA training does
exist (low-VRAM INT8 path lands on a 32 GB 5090), so an LTX Technicolor LoRA is *possible* later —
but that is a training project, not a download.

## E. What to do with this, in one pass

1. Pull section A into `models/loras/krea/` on the 4090 with a Civitai API token (helper script at
   `E:\comfymodels\models\loras\krea\_technicolor_dl.sh`, four files ≈ 890 MB; add
   `-H "Authorization: Bearer $TOKEN"` and delete the two ~9.8 KB stubs the token-less run left).
2. Pull section B onto the 5090: `bash tools/download_5090_models.sh lora-technicolor`.
3. First still test (4090, cheap, ~seconds): one existing FNI character ref +
   `krea2_<CHAR>` character LoRA + Technicolor LoRA #1 at 0.7 vs Peplum #2 at 1.0 vs no style LoRA,
   same seed, same prompt. Verdict = does the character survive and does it read Technicolor.
4. Then one comparison chunk: Krea-2-styled first frame → H3 FL2VA with the 80s Fantasy Movie H3
   LoRA at 1.4 (turbo compensation) vs the same chunk with `retro-fantasy` at 1.0 vs no style LoRA.
