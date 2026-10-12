# r/StableDiffusion — "Minimax H3 veterans (share your wisdom)"

Source: https://www.reddit.com/r/StableDiffusion/comments/1x34suo/minimax_h3_veterans_share_your_wisdom/
Pulled: 2026-10-11. 23 comments.

## OP problem
H3 works well on the first seed; re-rolling seeds makes it hallucinate / "deep-fry",
going off-prompt. RAM+GPU clears don't fix it. Only fix OP found: change the prompt
meaningfully so the model rethinks from scratch.

## Consensus fixes for seed instability
- RESTART ComfyUI. Multiple users (Kenchai, hdean667, Only4uArt) report a plain
  Comfy restart fixes it cold. Matches the raw/deep-fried renders we saw.
- Don't tune a prompt against one fixed seed and expect it to generalize (Entert-AI).
- Check for a leftover prompt line or a LoRA you forgot to remove (More-Ad5919).

## Turbo / Lightning LoRA — challenges our 4-step @ strength 1.0 plan
- Brad12d3 (top, 22): speedup nodes hurt quality, ESPECIALLY ref2video. Dropped
  Turbo Loras entirely; uses only memory-efficient Sage attention. "you'd end up
  spending more time rendering several bad clips as opposed to one or two longer
  good ones."
- No_Taste_4102: nothing beats full 20+ steps; runs ref2v_turbo_4step at ONLY 0.4
  strength, 25 steps, + Spectrum, 720 native.
=> Our refrun.py uses the 4-step LoRA at strength 1.0 / 4 steps. Reconsider:
   either drop the LoRA (full steps) or use it at low strength (0.4) at 20-25 steps.

## ref_image_size: match vs max
- dramaton42: `match` scales refs to render res (480p first pass, 960p on upscale).
  `max` = "more detail knowledge of your reference images". We use `match`; use `max`
  when identity fidelity matters more than speed.

## Model choice: base ref2va vs hybrid
- dilinjabass: base ref model "is absolute crap"; uses
  minimax_h3_hybrid_fl2va_ref2va_b20-49-int8 in full production.
- dramaton42: hybrid looks better but has WORSE reference adherence — "multiple
  images of Link with no sword or shield and it goes and adds BOTH."
  We chose base ref2va; dramaton42 backs base for fidelity. Live tension.

## Prompting doctrine (aligns with our 6-field grammar)
- Say what you want, never what you don't. "do not generate a third hand" CAUSES
  the third hand.
- The model fills gaps: kemb0 — add "her lips are closed throughout" to stop
  un-prompted blabbing. H3 invents speech if you don't constrain it. RELEVANT to us:
  always state lip/mouth behavior when a character is silent on-screen.
- Bitlovin: in ref2va mode H3 needs little — "use the video to drive the motion,
  wardrobe, timing, performances, audio, replace X with Y." Keep the prompt lean.
- Always-apply reference summary reduces hallucinations (per the altoiddealer WF).

## Other gems
- H3 as an upscaler (SecretSteel): render at 0.1mp, feed the video back with a short
  "upscale this" prompt to 0.5/1.0mp. Fails above 1.0mp (model isn't designed for 1920).
  External videos must be converted to ~640x360 @ 24fps (or 12fps for speed).
- Every H3 generation embeds its workflow JSON as video metadata — recoverable from
  any output.
- Attention backend -> "comfy kitchen"; schedulers er_sde / sgg_uniform (SecretSteel).
- Hybrid loader: minimax_h3_hybrid_fl2va_ref2va_b25-49-int8 — "no one uses base t2v
  or rftv anymore" (SecretSteel).
- Timeline / seed-hunter workflows (obvpm) for extending past 30s.
  See: mini_video_editor_timeline_node_for_h3_extend.
