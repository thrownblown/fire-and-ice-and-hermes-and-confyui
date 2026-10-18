# workflowtesting — triage verdicts (2026-10-15)

15 PNGs, all rendered on the 5090 (single counter series 00295→00369; input files
recovered from the 5090 ComfyUI input/ via /view?type=input). Triaged by side-by-side
VLM comparison against each run's actual source images.

## Group 1 — H3 stills (Teegra, "chained to purple/bronze chaise")

Graph: MiniMaxH3ReferenceToVideo → FizgigH3StillLatent/FizgigH3StillDecode → SaveImage,
2720x1536, length=5, ref_image_size=max, CLIP qwen3vl_32b_heretic_minimax_h3_nvfp4.
Alex's verdict: H3 generates stills well — confirmed: all four hold Teegra canon
(long black hair, green eyes, pale skin, purple two-piece, gold necklace). Shared
flaws: soft focus, harsh lighting, slightly stiff/plastic hands; no microtext.

| file | unet | LoRAs | seed | refs | verdict |
|---|---|---|---|---|---|
| ComfyUI_00295 | 10Eros_Max_h3_TURBO-hybrid_beta4_int8_convrot | Pokies@0.65 + retro-fantasy@1.5 | 162083016298228 | fkjdhtzbicof1.png, images1.jpg, bh0lgajcicof21.png | borderline — hair reads dark-brown in highlight, necklace reads black-beaded w/ pendant (not gold) |
| ComfyUI_00296 | same | same | 162083016298229 | same | KEEPER — vivid green eyes, gold beaded trim |
| ComfyUI_00368 | h3ErosMax_beta6_int8 | Pokies@1.0 + retro-fantasy@1.2 | 162083016298294 | 5x 960x* Teegra stills | KEEPER |
| ComfyUI_00369 | same | same | 162083016298295 | same | KEEPER |

Note: retro-fantasy style LoRA runs 1.2–1.5 stacked on the turbo unet — consistent
with the raise-style-LoRA-over-turbo rule.

## Group 2 — qwedit garment flat-lay extractions

Graph: Qwen-Rapid-AIO-NSFW-v22 (CheckpointLoaderSimple) + TextEncodeQwenImageEditPlus,
4 steps, Power Lora Loader empty (no LoRA on this stage), 4 LoadImage refs per run
(teegra_montage.png + source + shot_00215_f00039.jpg + qwedit_00015_ (1).png).
Prompt: "remove the woman/man and extract place their outfit on a white background".

| file | source | seed | fidelity vs source | verdict |
|---|---|---|---|---|
| qwedit_00008 | ComfyUI_00189 (Teegra multi-view sheet) | 656201155848237 | exact — lavender string bikini, black cord halter, gold fan clasp, beaded strings, thong | KEEPER |
| qwedit_00011 | same | 214519493684555 | drift — hallucinated lavender ribbon/bow neck tie + reworked hardware | fail (seed-dependent accessory hallucination) |
| qwedit_00022 | ComfyUI_00033 (JAROL ref) | 223847339779027 | faithful — maroon fur-trim tunic, gold necklace, belt, boots; nothing dropped/invented | KEEPER |
| qwedit_00025 | ComfyUI_00085 (ROLIEL ref, female) | 1001874406667019 | perfect match — light-blue gown, choker, belt. Prompt said "the man"; gender noun ignored, no harm | KEEPER |
| qwedit_00029 | NEKRON_r04_00001 | 975683277520122 | high fidelity BUT invented indigo chest panel over the bare-chest V (modesty patch) and dropped wrist cuffs | partial — usable if chest panel acceptable |
| qwedit_00034 | JULIANA_r04_00001 | 331132204460304 | faithful — deep-purple gown, bell sleeves, black trim | KEEPER |

## Group 3 — extract-outfit_v3 + clothtransfer two-stage (Qwen-Rapid-AIO, 8 steps)

Stage 1 (extract-outfit_v3@1.0, seed 149409673121358, source ComfyUI_00350 scene):
"extract the full body and the full outfit from front and from back onto a white background".
Stage 2 (clothtransfer@1.0, garment = qwedit_00004_ (1).png, pose = pose_ref.png):
dresses the pose-ref figure in the extracted garment.

| file | stage | verdict |
|---|---|---|
| ComfyUI_00351 (1024x1024) | 1 turnaround | KEEPER — real front+back views, garment exact vs source. CAVEAT: face is an anonymous model, not Teegra — turnarounds lose identity; pair with face refs downstream |
| ComfyUI_00352 (1360x768) | 2 | KEEPER — clean transfer, pose/bg consistent |
| ComfyUI_00353 (1920x1088) | 2 | KEEPER — clean transfer (stage2 seed 844848029830752, same as 00352 run) |
| ComfyUI_00356 (1920x1088) | 2 | fail — lower abdomen/hip melt (seed 347388586030439) |
| ComfyUI_00357 (1920x1088) | 2 | KEEPER — clean transfer (seed 147117159130011) |

## Failure modes observed (the "mixed bag")

1. Seed-dependent accessory hallucination on flat-lay extraction (00011 ribbon tie) —
   same source+prompt, adjacent seed.
2. Modesty-patch invention on bare-chest sources (00029 chest panel) + small drops (wrist cuffs).
3. Occasional hip/lower-abdomen melt in clothtransfer (00356) — re-roll seed.
4. Turnaround stage swaps the character's face for a generic model (00351).
5. H3 stills: soft focus + stiff hands; identity drift risk in jewelry color (00295).

## Status

- Keepers stay in this folder; filing into the asset library is blocked on
  docs/asset-schema.md, which the prompt-crafter contract references but does not exist yet.
- Source inputs recovered to %TEMP%\wt_inputs (ComfyUI_00189, ComfyUI_00350, pose_ref,
  qwedit_00004_ (1), qwedit_00015_ (1)); comparison montages in the Hermes scratch dir.
