# H3 Reddit research — 2026-11-04
<!-- spicy-ok: quotes Reddit thread titles, subreddit names and model ids verbatim from the sources -->

Three threads pulled at Alex's request. Post bodies + full comment trees came from the
arctic-shift archive API (`/api/comments/search?link_id=`, `limit=100`), which is
complete for threads older than ~a day; the third entry is a re-check of a comment
permalink already digested on 2026-10-31. External artifacts (GitHub / HuggingFace)
were verified through their own APIs on 2026-11-04; counts and dates below are as
returned, nothing paraphrased from memory.

Thread ids: `1xlaj6u`, `1xl8hgc` (both posted 2026-11-01), `1xif258` (2026-10-29, re-check).

---

## 1. "Why doesn't MiniMax H3 understand simple, direct instructions in prompts?" — r/StableDiffusion `1xlaj6u`

- permalink `/r/StableDiffusion/comments/1xlaj6u/why_doesnt_minimax_h3_understand_simple_direct/`
- zeroedit, score 29, posted 2026-11-01 15:50Z, `num_comments: 44` (43 rows returned).
- Ask: asking for "<Subject 1> is standing and facing the camera, and you can see them from
  head to thighs" crops the head off (chest-to-legs framing). Adding a *behaviour* to the
  head — "They are looking directly at the viewer and smiling" — brings the head back.
  Why must a body part be DOING something to be included?

### Consensus (this is the useful part)

**The training captions are VLM scene-graph descriptions — objects, attributes, actions,
relations — never framing instructions.** So "you can see them from head to thighs" is
vocabulary the captioning model never wrote, and the generator has no meaning for it. The
top three comments converge on this:

- u/the_bollo (64): "It's not a MMH3-specific thing" — every natural-language model.
- u/Quirky-Waltz1099 (63): "you're not telling it to frame a shot, you're describing what's
  in the scene. if the head isn't doing anything noteworthy … the model can just deprioritize
  it as filler space." Same fix for hands: "hands visible" does nothing, "hands gently clasped
  in front" works — **the model needs an action to anchor the body part in the frame.**
- u/KjellRS (7) and u/theqmann (12): captions are VLM scene graphs; camera framing, nose
  shape, foliage detail are simply absent from the training text, so the model has no idea
  what to do with those prompt tokens. "To make sure something is in the image, simply
  describe it."
- u/darkshark9 (1): "You can see them" is not vocabulary the labelling LLM used — describe
  the thing in detail instead.

**Where filmmaking vocabulary does and doesn't help.** u/Slight-Living-8098 (28) prescribes
shot names (Cowboy / American Shot = mid-thighs up; Medium Long Shot = knees up; Long Shot =
head to toes) *and* the reply chain settles the split: camera terms work for **zoom, angle,
view** (u/thebaker66, 5); they do not carry composition. u/DavLedo (2) and u/Danny_Stock (3)
push back that framing terms are inconsistently trained. Practical extras that repeat:
describe wardrobe or stance instead of the frame ("jeans" buys you a medium shot;
u/LuckyEsq 27, u/Qancho 6), phrase it as a **cowboy shot** (u/Bitlovin, u/QuarterDistinct857),
"Subject head to thigh in frame", keyframe init/final images (u/graceus777),
supply a reference image of the framing you want (u/bstr3k 2, u/SSj_Enforcer),
and — new to us — **the model reads a literal camera as a scene object**, so say "talking
directly to the **viewer**" instead (u/CorpPhoenix). u/ng5554: "shooting from a fixed tripod …
maintains that constant focal distance" stops the unintended zoom.

### The authoritative bit (worth acting on)

u/Slight-Living-8098 (8) quotes **MiniMax's own camera-control page** and its 3-field example
prompt — verbatim format is ours:

```
integrated_multimodal_description: [Shot 1] Live-action, cinematic, a medium-wide shot frames a
watchmaker at a cluttered bench under a single warm desk lamp. The camera pushes in with small
amplitude at slow speed toward the open watch case between his hands. He sets down the tweezers
and turns the movement a quarter turn to catch the light.

overall_soundscape: A low room tone carries throughout, broken by the tick of the movement, the
light clink of tweezers on wood, and a single chair creak

non_diegetic_music: Sparse piano notes at a slow tempo with a sustained string pad underneath
```

Camera control in H3 is **prompt-text only, over a fixed vocabulary of 20 motion types**
(section 4.3 of the Video Prompt Writing Guide that ships with the weights — i.e. the
`docs/h3-official/VIDEO_PROMPT_WRITING_GUIDE_base_en.md` we already vendor). Third-party
reference: `minimax3.com/tools/h3-camera-control` (fan site, but it cites the official
`huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md`
and lists the 20 phrases: Static Shot, Push In, Pull Out, Zoom In, Zoom Out, Pan Left/Right,
Truck Left/Right, Tilt Up/Down, Pedestal Up/Down, Arc Shot, Tracking Shot, POV, Roll
Clockwise/Counterclockwise, Shake Slightly/Strongly; amplitude {small|medium|large} and speed
{slow|normal|fast} modifiers, neither applying to Static Shot, POV or Shake). Its three stated
failure habits: **an invented verb** ("camera moves left" is not in the vocabulary),
**no target for the move** (every official example ends on what the lens lands on —
"toward the folded letter"), and **the move buried as trailing style tags** rather than written
as a natural action inside the sentence. Single shot = single move; a second shot is the only
way to change direction inside one clip. (A third-party builder page is not authority — the
vocabulary claim is checkable against our local copy of §4.3, which is the thing to diff.)

FNI read: our shot_type/angle grid (XWS…ECU) is exactly the class of token the thread says the
model under-weights. The cheap test this suggests is an **anchor clause** in the same sentence —
name the visible parts/wardrobe/action at the framing we asked for — measured against the current
prompt on a scene whose framing already drifts. Also: verify our camera-motion phrasing against
the guide's 20 phrases, and stop writing "you can see X"; write what X is doing.

---

## 2. "How are people replacing characters in porn so consistently" — r/comfyui `1xl8hgc`

- permalink `/r/comfyui/comments/1xl8hgc/how_are_people_replacing_characters_in_porn_so/`
- likingfirst, score 130, posted 2026-11-01 14:30Z, `num_comments: 51` (55 rows returned).
- Ask (NSFW-framed, but the technique is generic identity replacement): the same clip appears
  with two different people and it is seamless. Tried H3, Wan Animate, SCAIL, LTX, Krea
  first-frame + mvmnt — "nothing comes close"; Wan Animate is closest but won't do NSFW.
  OP's own diagnosis, later in the thread: H3 either doesn't replace the person or replaces
  them partially; character sheets got a few OK results — "is the secret some special NSFW base
  model?"

### What actually works (verified artifacts)

| artifact | verification 2026-11-04 |
|---|---|
| `huggingface.co/akatz-ai/MiniMax-H3-Character-Swap-LoRA` | 140,258 downloads, 710 likes, last modified 2026-10-17; tags `minimax-h3`, `lora`, `character-swap`, `video-editing`, `ref2va`, `video-to-video`, base `Comfy-Org/MiniMax-H3`, dataset `akatz-ai/H3-Character-Swap-v1`. Named by u/generate-addict (5) and confirmed by OP: "thats the lora i used … my issue with it was consistency but it seems the prompt matters more than I thought". |
| `github.com/D3voz/openjutsu` ("OPENjutsu") | 1,644 stars, MIT, pushed 2026-10-30; description: "One-click character swap for videos: an open-source, local Higgsfield Genjutsu alternative built on ComfyUI and MiniMax H3, with FLUX.3 Klein relighting." README: drop a video + a character photo → the main person is replaced, **camera, cuts, motion and soundtrack stay**; also hair/clothes change, object removal, relocation. Stack: **MiniMax H3 for video, SAM 3.1 to track people, Qwen3-VL 8B to describe pictures/frames and write prompts**; Next.js front end over a ComfyUI workflow via `@comfyorg/sdk`, modelled on Comfy's `comfy-reshoot`; workflow `workflows/simple.api.json` exported from `H3 One-Click Single Swap (DMAD 6 step).json`; describer alternatives Qwen3-VL 8B INT8 (default) / Qwen3-VL 4B FP8 / Gemma 4 E2B INT8, installed as single-file models in `ComfyUI/models/text_encoders`. |
| `github.com/Comfy-Org/comfy-openjutsu` | Comfy-Org's own clonable character-swap app + development guide, 81 stars, MIT — the upstream pattern Openjutsu follows. |
| `github.com/Bambushu/h3-recast` (from the challenge list, not this thread) | swaps **up to three people in one pass** with MiniMax H3 + a BFS LoRA, keeps motion/set/audio, optional FaceRefine lip pass; 16 GB VRAM / 64 GB RAM. |

**OP's verdict, bottom of the same chain:** u/likingfirst (8) "ok final update, this is hands
down the best one, the actual answer to my question. Good quality, good speed/performance, easy
to use … Generation is also unlimited because it's done in chunks" — that is OPENjutsu, reached
via u/MrFlores94 (36) "It's always a prompting issue. However there is a new alternative…".
Earlier on the same tool: "doesn't work for [mouth occlusion] but it's fast with good results
for other stuff … it could be because I'm not using a NSFW-friendly text_encoder … this shows
the mask it uses, I guess manually masking will get the most perfect result". One dissenting
data point: u/Phreak44444 — "I tried using this, didn't replace anything."

Other levers named in-thread: **full-precision models, especially the text encoder** give
noticeable prompt-adherence gains (u/35point1); Krea LoRA + Krea reference pose/character
sheet into H3 (u/OfficeMagic1); latent upscaling + character swap wired into any 6 GB ref2va
workflow (u/AI-Make-NSFW-Stuff, 8); Mysticxxx LoRA when a body part generates badly; Seedance 2.5
ref2video via the Oxen.ai API as an uncensored hosted fallback. Top comment (86) points at the
author's r/DegenDiffusion guide `/s/ozYegQ63Fs` — a share link, login-gated for anonymous
readers (the known `/s/` wall), not chased.

FNI read: this is the **identity-transfer** route to our consistency problem — H3 + a swap LoRA
on an existing clip, with SAM 3.1 tracking and a VLM writing the per-shot description, instead
of sheets/refs per setup. The Qwen3-VL 8B describer in OPENjutsu is the same model as our LM
Studio vision quiver, and "keep camera/cuts/motion/audio, replace the person" is precisely what
a re-cast of a rendered take would need. Mitosis/parts and camera drift are the reported failure
modes; OP's consistency complaint is about prompting, not the LoRA.

---

## 3. Re-check — `1xif258` comment permalink `19rv7151xjqv7` (r/StableDiffusion, digested 2026-10-31)

Re-pulled on request. **Nothing has changed:** still top-level (`parent_id: t3_1xif258`), score
**6** (was 6), **0 replies**, created 2026-10-30 05:46Z. The thread's newest comment is
u/thevegit0's 2026-10-30 22:42Z ("literally any uncensored llm … swapped to an rp gemma4 31b,
it's better at it somehow"), i.e. the thread is dead since 2026-10-30. Full verbatim system
prompt and both model ids are already in `docs/h3_reddit_research_2026-10-31.md` — no re-copy here.

**The open lead from that digest is now checkable and the answer is NO:** xb1n0ry announced his
own "enhanced reference node … automatic prompt writer and enhancer using local gguf models"
"today or tomorrow" (2026-10-30). His GitHub user has exactly 5 repos, newest pushed
**2026-10-18** (`ComfyUI-MOSS-Prompt-Enhancer`); nothing H3-prompt-related has appeared as of
2026-11-04. Do not go looking for it again until he posts.

Also visible now (not in the Oct-31 digest): u/Affectionate_Oil28 posted his own visualizer
attempt as `/r/StableDiffusion/s/RjMjFsHY5h` — the second of the two dead `/s/` links, still
login-gated; and the official repo pointer u/-Star-Walker- gave is
`huggingface.co/MiniMaxAI/MiniMax-H3/tree/main/docs` (the docs tree we already mirror in
`docs/h3-official/`).

---

## Cross-thread lead: the #OpenSourceHiggsfield challenge corpus

Surfaced by thread 2 (u/MrFlores94, then the OP) and worth its own line because it is a whole
suite of open, H3/LTX/Wan-based building blocks:

- `jutsustudio.com/open-source-higgsfield/` — an independent list of **102 entries** from ComfyUI's
  October-2026 challenge (Higgsfield had promised to open-source its platform and hadn't; Comfy
  and partners put up $25,000; ComfyUI shipped **OPENjutsu** on 2026-10-26; Higgsfield sent a
  cease-and-desist on 2026-10-29; submissions closed 2026-10-30). Star counts on that page are
  "as of November 1, 2026" and lag the live API (OPENjutsu shows 910 there vs 1,644 from the
  GitHub API today).
- Beyond the swaps: `roadmaus/ComfyUI-Continuity` (139 stars — one node for video+stills, `@`
  media refs, six model families), `jtydhr88/ComfyArt` (411), `wexloops/openfield` (124),
  `thePloggy/CreatorOS-Studio` (45 — one recurring character through camera moves, effects,
  talking avatars, motion transfer, editor), `szprivate/agentY` (46), `lucataco/open-source-higgsfield`
  ("Body Double", 45 — swaps actors in a clip, open weights only).
- The page says a submission list of the winners/top entries is kept there; u/MrFlores94 said
  winners were to be announced around the 6th (deadline extended to the 3rd). Re-check after
  2026-11-06 if wanted.

## Bottom line for the project

1. **Framing tokens are not instructions.** Cover the requested frame with described content and
   action in the same sentence; never "you can see X". Cheapest test: one anchor-clause prompt
   vs the current one on a drifting setup.
2. **Camera motion has a fixed 20-phrase vocabulary** in §4.3 of the guide we already vendor —
   diff our camera phrasing against it, and give every move a target to land on.
3. **Character swap is a real alternative to sheets for consistency**, and the two artifacts to
   read are `akatz-ai/MiniMax-H3-Character-Swap-LoRA` (HF, 140k downloads, ref2va) and
   `D3voz/openjutsu` (MIT, 1.6k stars) — the latter is a Next.js+ComfyUI app, so treat it as a
   workflow to mine (`workflows/simple.api.json`, DMAD 6-step), not something to run as-is.
4. Nothing here overturns the six-field REF2VA grammar or the 3-field FL2VA one; the camera-page
   example confirms the 3-field shape we already emit.
