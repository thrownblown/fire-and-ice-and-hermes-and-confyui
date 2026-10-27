# Qwen-Image / Qwen-Image-Edit prompting — Reddit digest (2026-10-27)

Mined from r/StableDiffusion, r/comfyui, r/drawthingsapp via arctic-shift
(10 threads, ~250 comments; raw JSON in
`scratch/qwen_reddit/threads.json`). Scope: prompting doctrine for the Qwen-Edit
steps of the FNI pipeline — `tools/qwen_scene.py` (character-into-scene
compose), the wardrobe/garment swap pass, and the restyle pass. Index entry in
`docs/h3_reddit_threads.md`.

## The doctrine (what changes our prompts)

1. **Identity-preservation clause goes AFTER the action/pose instruction.**
   (u/DrinksAtTheSpaceBar, 1ovaew7) "Put the identity preservation instructions
   after the reposing instructions — Qwen is much more likely to latch onto the
   original character pose if you prioritize preservation." Our
   `build_scenes.scene_prompt` currently puts "Keep the character's face, hair
   and costume unchanged" BEFORE the framing instruction. A/B candidate (see
   Test below).

2. **Address refs by slot: "the person in image 1 ... in image 2".**
   (u/sci032, 1ovaew7) `maintain the identity of the person in image1. maintain
   the identity of image2. the person in image1 is holding a spear while
   kneeling in image2` — then vary only the last line for action/pose. Directly
   matches our `--base`/`--ref2`/`--ref3` slots.

3. **Say "same person" / "this person", not gendered nouns.** (1o9r8e2)
   "same person" yields more uniform outcomes than "same girl/woman/man".
   "This person is kneeling with a spear in this background. Keep the facial
   identity of this individual."

4. **Don't describe the background when a ref supplies it — say "this
   background".** (1ovaew7 comments) Over-describing the scene fights the ref;
   let the image carry it. Tension with our scene_prompt, which describes the
   setting in prose BECAUSE we compose from a bare character sheet with no
   background ref — keep the prose only while there is no background/plate ref
   wired in; once a plate feeds --ref2, switch to "this background".

5. **Anti-drift clauses that work:** "Keep everything else unchanged",
   "Preserve face/clothing features", per-task preserves ("Preserve folds,
   stitching, and lighting" for garment edits). For stubborn drift: mask the
   change region (inpaint) — prompt wording alone has a ceiling (1xgpezp).

6. **Chain 2–3 small edits instead of one overloaded edit** (1n1n81o playbook).
   Matches the pipeline's stage-split instinct (compose scene first, wardrobe
   swap second) — do not fold scene + wardrobe + lighting into one prompt.

7. **Style transfer order: style-source first.** (u/Quick_Knowledge7413,
   1wlt9t9) "Take the style of <image 2> and apply it to <image 1>" beats
   mentioning the target first.

8. **Swap template that "breaks if you change a word"** (1nuu6k3 comments):
   "Substitute the individual in image 1 with the individual from image 2,
   ensuring the same pose, lighting, background, and attire from image 1 are
   preserved. Retain the facial characteristics and body proportions of the
   individual in image 2." — the rigid replace/preserve contract; same shape as
   the H3 character-swap LoRA prompt.

9. **Consistency LoRA exists for big edits:** Civitai 1939453
   "QwenEdit Consistence LoRA" — 0.15–0.3 for a single ref, 0.5–1.2 for 2+
   refs; try v1 and v2. For minor edits a "maintain the facial identity"
   clause suffices (1p11vaa). Candidate for the creature/weak-anatomy chars
   if scene composes keep breaking identity.

10. **The official HF Spaces "Edit Instruction Rewriter" system prompt**
    (1mudj7i) is a concise-prompt doctrine: preserve intent, add minimal
    category/color/size/position detail, "Replace Y with X" template, style
    description last. It ships inside ComfyUI's own qwen text-encoder template
    (`comfy/text_encoders/qwen_image.py`) and pairs with qwen-vl-max / a local
    LLM as a pre-rewrite stage. Our `core/prompt_edit_system.md` should be
    diffed against it.

11. **Image→video wording trick** (1nuu6k3 comments): run the still through
    Qwen2.5-VL (72B ideal, bf16 7B floor) to get the *wording* of the image,
    then feed that wording into the video model's prompt. For us: caption the
    APPROVED scene still with the goldfishbowl 32B and seed the H3 scene
    prompt's `detailed_description` from that caption instead of hand-written
    scene text. Cheap, testable.

12. **Viewpoint/camera rotation responds to Chinese commands** (1nuu6k3):
    从背面视角 (view from back), 从侧面90度观看场景 (view scene from the side
    90°) etc. execute more reliably than English for rotation tasks. Niche —
    file under camera-turnaround work, not scene compose.

13. **Workflow settings for full Qwen Image 2.1** (1wsgrh4, NOT our Rapid-AIO):
    40 steps, 4.0–4.2 MP for textless images, 2.0–2.5 MP for text-heavy,
    don't go below ~2.0 MP, no acceleration LoRA needed. Note: first ref image
    must stay under ~2048 total px or it silently fails to decode
    (1x675fb comments — "scale to total pixels" node, ~1.8 MP).

## Threads

| id | title | score | takeaway |
|---|---|---|---|
| 1n1n81o | Qwen-Image-Edit Prompt Guide: The Complete Playbook | 340 | 7-category prompt playbook (text/local/global/micro/identity/poster/camera); pro tips = doctrine #5/#6. Commenters suspect ChatGPT-authorship — treat examples as starting templates, verify on our renders. |
| 1wlt9t9 | QWEN Image 2.1 Edit tips | 454 | `<image 1>`/`<image 2>` slot syntax for pose/texture/lighting/style transfer; style-source-first rule (#7). |
| 1mudj7i | Qwen Image Edit System Prompt | 48 | the HF Spaces rewriter system prompt, verbatim (#10). |
| 1xgpezp | Stop Qwen Edit changing things you didn't ask it to | 0 | prompt ceilings → mask/inpaint (#5). |
| 1wsgrh4 | Make Qwen 2.1 design like GPT Image 2.5 | 15 | LLM-pre-structured prompts (composition/hierarchy before content); settings #13. |
| 1x675fb | How to refer to images? | 0 | multi-ref gotcha: name BOTH images in the prompt or one is ignored; 2048px decode ceiling (#13). |
| 1nuu6k3 | Qwen Image Edit 2509, helpful commands | 261 | Chinese viewpoint commands (#12); image→video wording trick (#11); rigid swap template (#8). |
| 1ovaew7 | Put a character in an environment in different positions | 9 | identity-after-action (#1); image1/image2 address (#2); "this background" (#4). |
| 1p11vaa | Character face consistency | — | Consistence LoRA strengths (#9). |
| 1o9r8e2 | Qwen Edit 2509 character consistency | — | "same person" wording (#3). |

## Concrete next test (doctrine → generation)

**T0026 — scene_prompt template A/B** on one char (taro), same seed, same
winner still, two composes:
- (a) current `build_scenes.scene_prompt` (identity clause early, "the
  character", prose scene).
- (b) doctrine rewrite: `The person in image 1 is <action> in this scene:
  <scene>. Full body, mid shot. Maintain the identity of the person in image
  1 — face, hair and costume unchanged. ...`
Judge: 32B review + eyeball identity hold. If (b) wins, patch
`build_scenes.scene_prompt` and re-compose any BAD-reviewed chars with it.
