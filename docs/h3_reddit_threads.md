# H3 Reddit Threads — index of relevant r/StableDiffusion reading

Purpose: a running index of community threads that inform the FNI H3 pipeline. Each entry:
link, why it matters, and the concrete takeaway. Per-thread digests go in their own
`docs/*_thread.md`; this is the map.

Status legend: [READ] digested in a separate doc · [TODO] known useful, not yet read.

---

## [READ] "Minimax h3 veterans (share your wisdom)"
- https://www.reddit.com/r/StableDiffusion/comments/1x34suo/minimax_h3_veterans_share_your_wisdom/
- Digest: `docs/h3_veterans_thread.md`
- Takeaway: seed instability → restart ComfyUI first; don't use the 4-step turbo LoRA at
  strength 1.0 for ref2video (full steps, or 0.4 strength); `max` ref_image_size for identity;
  say what you want not what you don't; state lip/hand behavior or H3 invents it.

## [TODO] "How much VRAM does H3 need? Less than you might think"
- https://www.reddit.com/r/StableDiffusion/comments/1vz2n7y/how_much_vram_does_h3_need_less_than_you_might/
- Cited in the veterans thread for low-VRAM setups. Relevant to the 4090/5090 split and any
  future lower-res preview pass.

## [TODO] "Mini video editor / timeline node for H3 extend"
- https://www.reddit.com/r/StableDiffusion/comments/1wmj6xr/mini_video_editor_timeline_node_for_h3_extend/
- The obvpm timeline workflow for extending past 30s and seed-hunting with references.
  Relevant to assembling long action sequences from per-chunk clips. Has a YouTube tutorial.

## [TODO] Character consistency (sparkleriley "part 2" + Lumibelle)
- Referenced in the FNI skill; source of the per-reference keep/drop retention lines and
  turntable REEL VIDEO identity refs. Locate the exact thread URLs and fill in.

## [TODO] RefMods / "refloras" (malcolmrey thread)
- Referenced in the FNI skill: RefMod nodes fed into the text encoder, per-subject tagging,
  audio voice-cloning refs. Locate exact URL.

## Backlog — search for
- H3 latent upscale / second-pass threads (the altoiddealer WF ships a latent upscale pass).
- H3 Spectrum speedup threads (xmarre ComfyUI-Spectrum-MiniMax-H3).
- H3 audio (dialogue/lip-sync) quality threads.
- Bakshi Fire & Ice or rotoscope-style LoRA threads, if any exist.
